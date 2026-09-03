"""
app/workflow/workflow_chain_detector.py

WorkflowChainDetector — detects connections between workflows in a workspace.

Completely deterministic, no LLM.

Detection runs three passes per (source_workflow, terminal_step) pair:

  Pass 1 — name_match (confidence 1.0)
    terminal_step.action == target_workflow.trigger.event_type exactly.
    Also tries common naming conventions:
      "disburse_loan" → "loan_disbursed", "loan_disbursement"
    Stored with status=auto (high confidence, no review needed).

  Pass 2 — fts_match (confidence = ts_rank, threshold 0.05)
    websearch_to_tsquery(terminal_step.action) against
    trigger tsvector (trigger_name + display_name + aliases).
    Stored with status=suggested (needs review).

  Pass 3 — rule_mention (confidence 0.7)
    Scans WorkflowActionMapping.applicable_rules for text that contains
    another workflow's trigger_name or workflow name.
    Stored with status=suggested.

Duplicate handling:
  Existing rows with status=accepted or rejected are never overwritten.
  Existing auto/suggested rows are deleted and re-inserted on each run
  so stale chains from deleted workflows are cleaned up.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.workflow import Workflow
from app.models.workflow_action_mapping import WorkflowActionMapping, MappingStatus
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workflow_chain import WorkflowChain, ChainMatchType, ChainStatus
from app.core.logger import logger

# ts_rank threshold for FTS match — below this value the match is too weak
_FTS_THRESHOLD = 0.05

# Confidence assigned to rule_mention matches
_RULE_MENTION_CONFIDENCE = 0.7


class WorkflowChainDetector:

    def detect(self, db: Session, workspace_id: int) -> list[WorkflowChain]:
        """
        Run chain detection for all workflows in the workspace.

        Returns the list of WorkflowChain rows that were created/updated.
        Persists results to workflow_chains table — caller must commit.
        """
        workflows = self._load_workflows(db, workspace_id)
        if len(workflows) < 2:
            return []

        action_mapping = self._build_action_mapping_index(db, workspace_id)

        # Delete stale auto/suggested rows — preserves accepted/rejected
        self._delete_stale(db, workspace_id)

        chains: list[WorkflowChain] = []

        for source_wf in workflows:
            terminal_steps = _extract_terminal_steps(source_wf)

            for step in terminal_steps:
                action = step["action"]

                for target_wf in workflows:
                    if target_wf.id == source_wf.id:
                        continue

                    trigger_name = _get_trigger_name(target_wf)
                    if not trigger_name:
                        continue

                    # ── Pass 1: name match ────────────────────────────────
                    if _names_match(action, trigger_name):
                        chain = self._make_chain(
                            db, workspace_id,
                            source_wf, step, target_wf, trigger_name,
                            ChainMatchType.name_match, 1.0, ChainStatus.auto,
                        )
                        if chain:
                            chains.append(chain)
                        continue  # name match is definitive — skip FTS

                    # ── Pass 2: FTS match ─────────────────────────────────
                    fts_score = self._fts_score(
                        db, action, target_wf.id
                    )
                    if fts_score and fts_score >= _FTS_THRESHOLD:
                        chain = self._make_chain(
                            db, workspace_id,
                            source_wf, step, target_wf, trigger_name,
                            ChainMatchType.fts_match, float(fts_score),
                            ChainStatus.suggested,
                        )
                        if chain:
                            chains.append(chain)
                        continue

                    # ── Pass 3: rule mention ──────────────────────────────
                    if self._rule_mentions_target(
                        action, action_mapping, trigger_name, target_wf.name
                    ):
                        chain = self._make_chain(
                            db, workspace_id,
                            source_wf, step, target_wf, trigger_name,
                            ChainMatchType.rule_mention, _RULE_MENTION_CONFIDENCE,
                            ChainStatus.suggested,
                        )
                        if chain:
                            chains.append(chain)

        db.flush()
        logger.info(
            "workflow_chains_detected",
            extra={"extra_data": {
                "workspace_id": workspace_id,
                "chains_found": len(chains),
            }},
        )
        return chains

    # ── Loaders ───────────────────────────────────────────────────────────────

    def _load_workflows(self, db: Session, workspace_id: int) -> list[Workflow]:
        return (
            db.query(Workflow)
            .filter(
                Workflow.workspace_id == workspace_id,
                Workflow.status == "active",
                Workflow.parsed_rule_json.isnot(None),
            )
            .all()
        )

    def _build_action_mapping_index(
        self,
        db: Session,
        workspace_id: int,
    ) -> dict[str, WorkflowActionMapping]:
        """Map action_name → its WorkflowActionMapping row (with applicable_rules)."""
        rows = (
            db.query(WorkflowActionMapping)
            .join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowActionMapping.workflow_knowledge_id,
            )
            .filter(
                WorkflowKnowledge.workspace_id == workspace_id,
                WorkflowActionMapping.status == MappingStatus.MAPPED,
                WorkflowActionMapping.action_name.isnot(None),
            )
            .all()
        )
        index: dict[str, WorkflowActionMapping] = {}
        for row in rows:
            if row.action_name:
                index[row.action_name] = row
        return index

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _fts_score(
        self,
        db: Session,
        action_name: str,
        target_workflow_id: int,
    ) -> float | None:
        """
        Compute ts_rank of action_name query against the target workflow's
        trigger tsvector (trigger_name + display_name + aliases).
        Returns None if no matching trigger mapping found.
        """
        try:
            query_str = action_name.replace("_", " ")
            result = db.execute(
                text("""
                    SELECT ts_rank(
                        to_tsvector('english',
                            coalesce(replace(wtm.trigger_name, '_', ' '), '') || ' ' ||
                            coalesce(wtm.display_name, '') || ' ' ||
                            coalesce(wtm.catalog_description, '')
                        ) ||
                        jsonb_to_tsvector('english',
                            coalesce(wtm.aliases, '[]'::jsonb),
                            '["string"]'
                        ),
                        websearch_to_tsquery('english', :query)
                    ) AS rank
                    FROM workflow_trigger_mapping wtm
                    JOIN workflow_knowledge wk ON wk.id = wtm.workflow_knowledge_id
                    WHERE wk.workspace_id = (
                        SELECT workspace_id FROM workflows WHERE id = :wf_id
                    )
                    AND wtm.status = 'MAPPED'
                    AND wtm.trigger_name IS NOT NULL
                    AND to_tsvector('english',
                            coalesce(replace(wtm.trigger_name, '_', ' '), '') || ' ' ||
                            coalesce(wtm.display_name, '') || ' ' ||
                            coalesce(wtm.catalog_description, '')
                        ) @@ websearch_to_tsquery('english', :query)
                    ORDER BY rank DESC
                    LIMIT 1
                """),
                {"query": query_str, "wf_id": target_workflow_id},
            ).fetchone()
            return result[0] if result else None
        except Exception:
            return None

    def _rule_mentions_target(
        self,
        action_name: str,
        action_mapping: dict[str, WorkflowActionMapping],
        target_trigger_name: str,
        target_workflow_name: str,
    ) -> bool:
        """
        Return True if any applicable_rule on this action mentions
        the target trigger name or target workflow name.
        """
        mapping = action_mapping.get(action_name)
        if not mapping or not mapping.applicable_rules:
            return False

        target_trigger_lower = target_trigger_name.lower().replace("_", " ")
        target_workflow_lower = target_workflow_name.lower()

        for rule in mapping.applicable_rules:
            rule_lower = rule.lower()
            if target_trigger_lower in rule_lower:
                return True
            if target_workflow_lower in rule_lower:
                return True
            # Also check underscore form
            if target_trigger_name.lower() in rule_lower:
                return True

        return False

    def _make_chain(
        self,
        db: Session,
        workspace_id: int,
        source_wf: Workflow,
        step: dict,
        target_wf: Workflow,
        target_trigger: str,
        match_type: ChainMatchType,
        confidence: float,
        status: ChainStatus,
    ) -> WorkflowChain | None:
        """
        Create a WorkflowChain row if one does not already exist with
        status=accepted or status=rejected for this exact pair.
        """
        existing = (
            db.query(WorkflowChain)
            .filter(
                WorkflowChain.source_workflow_id == source_wf.id,
                WorkflowChain.source_step_id == step["id"],
                WorkflowChain.target_workflow_id == target_wf.id,
            )
            .first()
        )
        if existing and existing.status in (ChainStatus.accepted, ChainStatus.rejected):
            # User decision — never overwrite
            return None

        chain = WorkflowChain(
            workspace_id       = workspace_id,
            source_workflow_id = source_wf.id,
            source_step_id     = step["id"],
            source_action      = step["action"],
            target_workflow_id = target_wf.id,
            target_trigger     = target_trigger,
            match_type         = match_type,
            confidence         = confidence,
            status             = status,
        )
        db.add(chain)
        return chain

    def _delete_stale(self, db: Session, workspace_id: int) -> None:
        """Remove auto/suggested rows — they will be re-detected fresh."""
        db.query(WorkflowChain).filter(
            WorkflowChain.workspace_id == workspace_id,
            WorkflowChain.status.in_([ChainStatus.auto, ChainStatus.suggested]),
        ).delete(synchronize_session=False)
        db.flush()


# ── Pure helpers ──────────────────────────────────────────────────────────────

def _extract_terminal_steps(workflow: Workflow) -> list[dict]:
    """
    Return steps in the compiled DAG that no other step depends on.
    These are the natural exit points of the workflow.
    """
    dag = workflow.parsed_rule_json or {}
    steps = dag.get("steps", [])
    if not steps:
        return []

    # Collect all step IDs that appear in any depends_on list
    depended_on: set[str] = set()
    for step in steps:
        for dep in (step.get("depends_on") or []):
            depended_on.add(str(dep))

    return [s for s in steps if str(s["id"]) not in depended_on]


def _get_trigger_name(workflow: Workflow) -> str | None:
    """Extract the trigger event_type from a workflow's compiled DAG."""
    dag = workflow.parsed_rule_json or {}
    trigger = dag.get("trigger") or {}
    return trigger.get("event_type") or None


def _names_match(action_name: str, trigger_name: str) -> bool:
    """
    Check if an action name and a trigger name represent the same event.

    Exact match:
      "disburse_loan" == "disburse_loan"

    Past-tense convention:
      "disburse_loan"  → "loan_disbursed"
      "approve_loan"   → "loan_approved"
      "reject_application" → "application_rejected"
    """
    if action_name == trigger_name:
        return True

    # Try verb → past-tense event name: "approve_loan" → "loan_approved"
    parts = action_name.split("_")
    if len(parts) >= 2:
        # "approve_loan" → "loan_approved"  (reverse + past tense on verb)
        verb = parts[0]
        obj  = "_".join(parts[1:])
        past = _to_past_tense(verb)
        candidate = f"{obj}_{past}"
        if candidate == trigger_name:
            return True

        # "loan_disburse" → "loan_disbursed"  (append d/ed)
        candidate2 = f"{action_name}d"
        if candidate2 == trigger_name:
            return True

        candidate3 = f"{action_name}ed"
        if candidate3 == trigger_name:
            return True

    return False


def _to_past_tense(verb: str) -> str:
    """Very simple English past-tense suffix for common banking verbs."""
    irregulars = {
        "approve": "approved",
        "reject":  "rejected",
        "disburse":"disbursed",
        "verify":  "verified",
        "create":  "created",
        "generate":"generated",
        "send":    "sent",
        "notify":  "notified",
        "complete":"completed",
        "submit":  "submitted",
        "receive": "received",
        "process": "processed",
        "review":  "reviewed",
        "assess":  "assessed",
        "close":   "closed",
        "freeze":  "frozen",
        "block":   "blocked",
        "flag":    "flagged",
        "assign":  "assigned",
        "classify":"classified",
        "calculate":"calculated",
        "issue":   "issued",
        "repay":   "repaid",
        "collect": "collected",
    }
    return irregulars.get(verb, f"{verb}ed")
