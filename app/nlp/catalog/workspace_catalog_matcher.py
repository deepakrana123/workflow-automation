"""
app/nlp/catalog/workspace_catalog_matcher.py

WorkspaceCatalogMatcher — workspace-scoped catalog matching for generation.

Source of truth: WorkflowActionMapping and WorkflowTriggerMapping snapshot columns.
ActionDefinition and TriggerDefinition are NEVER queried here.

Matching strategy:
  1. Full-text search (websearch_to_tsquery) across snapshot columns:
       action_name, display_name, catalog_description, aliases
     This mirrors the BRD ingestion retrieval pipeline and handles natural
     language requests cleanly (AND by default, phrase support, no SQL errors).
  2. If full-text finds nothing (e.g. user request too terse or no tsquery tokens
     match), falls back to returning ALL mapped actions for the workspace so
     generation is never silently empty.

The workspace IS the filter — no global catalog rows ever enter.
selected_action_ids remains the only escape hatch for adding explicit globals.

IMPORTANT — deduplication:
  PostgreSQL DISTINCT ON requires the DISTINCT ON column to appear first in
  ORDER BY, which conflicts with ORDER BY rank DESC. We therefore fetch all
  matching rows ordered by rank and deduplicate in Python, keeping the
  highest-ranked row per action_definition_id / trigger_definition_id.
"""

from collections import Counter

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.workflow_action_mapping import WorkflowActionMapping, MappingStatus
from app.models.workflow_trigger_mapping import WorkflowTriggerMapping
from app.models.workflow_knowledge import WorkflowKnowledge
from app.nlp.catalog.matcher import CatalogMatchResult


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _majority_workflow_type(items: list, field: str = "workflow_type") -> str | None:
    counter: Counter = Counter()
    for item in items:
        wt = getattr(item, field, None)
        if wt:
            counter[wt] += 1
    return counter.most_common(1)[0][0] if counter else None


def _action_fts_vector(mapping):
    """Build the tsvector expression over action snapshot columns."""
    return func.to_tsvector(
        "english",
        func.concat(
            func.coalesce(func.replace(mapping.action_name, "_", " "), ""),
            " ",
            func.coalesce(mapping.display_name, ""),
            " ",
            func.coalesce(mapping.catalog_description, ""),
        ),
    ).op("||")(
        func.jsonb_to_tsvector(
            "english",
            func.coalesce(mapping.aliases, "[]"),
            '["string"]',
        )
    )


def _trigger_fts_vector(mapping):
    """Build the tsvector expression over trigger snapshot columns."""
    return func.to_tsvector(
        "english",
        func.concat(
            func.coalesce(func.replace(mapping.trigger_name, "_", " "), ""),
            " ",
            func.coalesce(mapping.display_name, ""),
            " ",
            func.coalesce(mapping.catalog_description, ""),
        ),
    ).op("||")(
        func.jsonb_to_tsvector(
            "english",
            func.coalesce(mapping.aliases, "[]"),
            '["string"]',
        )
    )


def _dedup_by_action(rows: list[WorkflowActionMapping]) -> list[WorkflowActionMapping]:
    """
    Deduplicate action mapping rows by matched_action_definition_id.
    Preserves the first occurrence (highest rank when called after ORDER BY rank DESC).
    Skips rows where action_name is None as a defensive guard.
    """
    seen: set[int] = set()
    result: list[WorkflowActionMapping] = []
    for row in rows:
        if row.action_name is None:
            continue
        key = row.matched_action_definition_id
        if key not in seen:
            seen.add(key)
            result.append(row)
    return result


def _dedup_by_trigger(rows: list[WorkflowTriggerMapping]) -> list[WorkflowTriggerMapping]:
    """
    Deduplicate trigger mapping rows by matched_trigger_definition_id.
    Skips rows where trigger_name is None as a defensive guard.
    """
    seen: set[int] = set()
    result: list[WorkflowTriggerMapping] = []
    for row in rows:
        if row.trigger_name is None:
            continue
        key = row.matched_trigger_definition_id
        if key not in seen:
            seen.add(key)
            result.append(row)
    return result


# ---------------------------------------------------------------------------
# Prompt line builders
# ---------------------------------------------------------------------------

def _action_prompt_line(m: WorkflowActionMapping) -> str:
    """
    Build one line for the {actions} prompt variable.

    Format (all parts optional — only added when data exists):
      action_name   [Rule: ...]   [Actor: ...]

    Examples:
      verify_property_title   [Rule: Title must be clean before disbursement]   [Actor: Legal Officer (verifier)]
      classify_npa
    """
    # action_name is guaranteed non-None here (callers filter before building lines)
    parts: list[str] = [m.action_name or ""]

    for rule in (m.applicable_rules or []):
        if rule:
            parts.append(f"[Rule: {rule}]")

    for actor in (m.responsible_actors or []):
        if actor:
            parts.append(f"[Actor: {actor}]")

    return "   ".join(parts)


def _trigger_prompt_line(m: WorkflowTriggerMapping) -> str:
    """
    Build one line for the {triggers} prompt variable.

    Format (same pattern as actions):
      trigger_name   [Rule: ...]   [Actor: ...]
    """
    parts: list[str] = [m.trigger_name or ""]

    for rule in (m.applicable_rules or []):
        if rule:
            parts.append(f"[Rule: {rule}]")

    for actor in (m.responsible_actors or []):
        if actor:
            parts.append(f"[Actor: {actor}]")

    return "   ".join(parts)


# ---------------------------------------------------------------------------
# Result assembly
# ---------------------------------------------------------------------------

def build_workspace_match_result(
    action_mappings: list[WorkflowActionMapping],
    trigger_mappings: list[WorkflowTriggerMapping],
    selected_action_mappings: list[WorkflowActionMapping] | None = None,
) -> CatalogMatchResult:
    """
    Assemble a CatalogMatchResult purely from mapping snapshot rows.

    Deduplicates by matched_action_definition_id / matched_trigger_definition_id
    (workspace-sourced first, then selected), preserving order.
    Rows with null action_name / trigger_name are silently skipped.
    """
    merged_actions: dict[int, WorkflowActionMapping] = {}
    for m in action_mappings:
        if m.action_name is None:
            continue
        merged_actions[m.matched_action_definition_id] = m
    for m in (selected_action_mappings or []):
        if m.action_name is None:
            continue
        merged_actions.setdefault(m.matched_action_definition_id, m)
    action_list = list(merged_actions.values())

    merged_triggers: dict[int, WorkflowTriggerMapping] = {}
    for m in trigger_mappings:
        if m.trigger_name is None:
            continue
        merged_triggers[m.matched_trigger_definition_id] = m
    trigger_list = list(merged_triggers.values())

    workflow_type = _majority_workflow_type(action_list + trigger_list)

    return CatalogMatchResult(
        workflow_type=workflow_type,
        matched_triggers=trigger_list,
        matched_actions=action_list,
        # Enriched lines: "action_name   [Rule: ...]   [Actor: ...]"
        # These go verbatim into the {actions} and {triggers} prompt variables.
        # The LLM is instructed to copy the name part exactly — context after
        # the name is informational only.
        trigger_names=[_trigger_prompt_line(m) for m in trigger_list],
        action_names=[_action_prompt_line(m) for m in action_list],
    )


# ---------------------------------------------------------------------------
# Matcher
# ---------------------------------------------------------------------------

class WorkspaceCatalogMatcher:
    """
    Matches workspace BRD-mapped actions/triggers against a user request.

    Reads exclusively from WorkflowActionMapping and WorkflowTriggerMapping
    snapshot columns. ActionDefinition and TriggerDefinition are never queried.
    """

    def __init__(self, db: Session):
        self.db = db

    def match(
        self,
        workspace_id: int,
        user_request: str,
        selected_action_ids: list[int] | None = None,
        brd_id: int | None = None,
    ) -> CatalogMatchResult:
        action_mappings  = self._workspace_actions(workspace_id, user_request, brd_id)
        trigger_mappings = self._workspace_triggers(workspace_id, user_request, brd_id)

        # selected_action_ids: explicit global overrides — still resolved via
        # WorkflowActionMapping so we get the snapshot, not ActionDefinition
        selected = self._selected_actions(workspace_id, selected_action_ids or [])

        return build_workspace_match_result(action_mappings, trigger_mappings, selected)

    # ── workspace action matching ────────────────────────────────────────────

    def _workspace_actions(
        self,
        workspace_id: int,
        user_request: str,
        brd_id: int | None = None,
    ) -> list[WorkflowActionMapping]:
        """
        Full-text search over action snapshot columns scoped to the workspace.

        When brd_id is provided, restricts to that single WorkflowKnowledge row
        so generation is grounded in one BRD only.
        Falls back to all mapped workspace actions when FTS matches nothing.
        """
        base_q = (
            self.db.query(WorkflowActionMapping)
            .join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowActionMapping.workflow_knowledge_id,
            )
            .filter(
                WorkflowKnowledge.workspace_id == workspace_id,
                WorkflowActionMapping.status == MappingStatus.MAPPED,
                WorkflowActionMapping.action_name.isnot(None),
            )
        )
        if brd_id is not None:
            base_q = base_q.filter(WorkflowActionMapping.workflow_knowledge_id == brd_id)

        fts_results = self._fts_actions(base_q, user_request)
        if fts_results:
            return fts_results

        # Fallback: all mapped workspace actions, deduplicated in Python
        rows = base_q.all()
        return _dedup_by_action(rows)

    def _fts_actions(self, base_q, user_request: str) -> list[WorkflowActionMapping]:
        """
        websearch_to_tsquery search over action snapshot columns.

        Fetches all matches ordered by rank DESC, then deduplicates in Python
        by matched_action_definition_id (keeping highest-ranked row per action).
        This avoids the PostgreSQL DISTINCT ON / ORDER BY conflict.
        """
        try:
            ts_query = func.websearch_to_tsquery("english", user_request)
            vector   = _action_fts_vector(WorkflowActionMapping)
            rank     = func.ts_rank(vector, ts_query)

            rows = (
                base_q
                .filter(vector.op("@@")(ts_query))
                .order_by(rank.desc())
                .all()
            )
            return _dedup_by_action(rows)
        except Exception:
            return []

    # ── workspace trigger matching ───────────────────────────────────────────

    def _workspace_triggers(
        self,
        workspace_id: int,
        user_request: str,
        brd_id: int | None = None,
    ) -> list[WorkflowTriggerMapping]:
        """
        Full-text search over trigger snapshot columns scoped to the workspace.

        When brd_id is provided, restricts to that single WorkflowKnowledge row.
        Falls back to all mapped workspace triggers when FTS matches nothing.
        """
        base_q = (
            self.db.query(WorkflowTriggerMapping)
            .join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowTriggerMapping.workflow_knowledge_id,
            )
            .filter(
                WorkflowKnowledge.workspace_id == workspace_id,
                WorkflowTriggerMapping.status == MappingStatus.MAPPED,
                WorkflowTriggerMapping.trigger_name.isnot(None),
            )
        )
        if brd_id is not None:
            base_q = base_q.filter(WorkflowTriggerMapping.workflow_knowledge_id == brd_id)

        fts_results = self._fts_triggers(base_q, user_request)
        if fts_results:
            return fts_results

        # Fallback: all mapped workspace triggers, deduplicated in Python
        rows = base_q.all()
        return _dedup_by_trigger(rows)

    def _fts_triggers(self, base_q, user_request: str) -> list[WorkflowTriggerMapping]:
        """
        websearch_to_tsquery search over trigger snapshot columns.
        Same deduplication approach as _fts_actions.
        """
        try:
            ts_query = func.websearch_to_tsquery("english", user_request)
            vector   = _trigger_fts_vector(WorkflowTriggerMapping)
            rank     = func.ts_rank(vector, ts_query)

            rows = (
                base_q
                .filter(vector.op("@@")(ts_query))
                .order_by(rank.desc())
                .all()
            )
            return _dedup_by_trigger(rows)
        except Exception:
            return []

    # ── explicit selection (global override) ─────────────────────────────────

    def _selected_actions(
        self,
        workspace_id: int,
        action_definition_ids: list[int],
    ) -> list[WorkflowActionMapping]:
        """
        Return mapping rows for explicitly selected action_definition_ids.

        Searches within the workspace's mappings so we get snapshot data.
        """
        if not action_definition_ids:
            return []

        rows = (
            self.db.query(WorkflowActionMapping)
            .join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowActionMapping.workflow_knowledge_id,
            )
            .filter(
                WorkflowKnowledge.workspace_id == workspace_id,
                WorkflowActionMapping.matched_action_definition_id.in_(
                    action_definition_ids
                ),
                WorkflowActionMapping.status == MappingStatus.MAPPED,
                WorkflowActionMapping.action_name.isnot(None),
            )
            .all()
        )
        return _dedup_by_action(rows)
