"""
app/nlp/catalog/workspace_catalog_matcher.py

WorkspaceCatalogMatcher — the workspace-scoped counterpart to CatalogMatcher.

Where CatalogMatcher grounds generation in the ENTIRE global catalog
(`action_repository.get_active()`), this matcher grounds it ONLY in:

  1. the ActionDefinition / TriggerDefinition rows that the workspace's BRDs
     already mapped to (via WorkflowActionMapping.matched_action_definition_id /
     WorkflowTriggerMapping.matched_trigger_definition_id), and
  2. any global actions the user EXPLICITLY selected (`selected_action_ids`).

It never calls `get_active()` on the global repositories, so the global catalog
can never leak into workspace-scoped generation. The workspace IS the filter —
there is no keyword/semantic narrowing here; the candidate set is small by
construction (~a dozen actions), which also keeps the prompt small.

Output is a `CatalogMatchResult` — identical in shape to CatalogMatcher's — so
the rest of the NLP pipeline (suitability, prompt, generation) is unchanged.
"""

from collections import Counter

from sqlalchemy.orm import Session

from app.models.action_definitions import ActionDefinition
from app.models.trigger_definitions import TriggerDefinition
from app.models.workflow_action_mapping import WorkflowActionMapping
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workflow_trigger_mapping import WorkflowTriggerMapping
from app.nlp.catalog.matcher import CatalogMatchResult


def _detect_workflow_type(items) -> str | None:
    """Majority workflow_type across the given definitions (triggers + actions)."""
    counter: Counter = Counter()
    for item in items:
        wt = getattr(item, "workflow_type", None)
        if wt:
            counter[wt] += 1
    if not counter:
        return None
    return counter.most_common(1)[0][0]


def build_workspace_match_result(
    actions,
    triggers,
    selected_actions=None,
) -> CatalogMatchResult:
    """Pure assembly of a CatalogMatchResult from workspace entities.

    Args:
        actions: workspace-mapped ActionDefinition-like objects (need .id, .name,
                 .workflow_type).
        triggers: workspace-mapped TriggerDefinition-like objects.
        selected_actions: explicitly user-selected global actions to add in.

    Deduplicates by id (workspace first, then selected), preserving order.
    """
    merged_actions: dict = {}
    for a in actions:
        merged_actions[a.id] = a
    for a in (selected_actions or []):
        merged_actions.setdefault(a.id, a)
    action_list = list(merged_actions.values())

    merged_triggers: dict = {}
    for t in triggers:
        merged_triggers[t.id] = t
    trigger_list = list(merged_triggers.values())

    workflow_type = _detect_workflow_type(trigger_list + action_list)

    return CatalogMatchResult(
        workflow_type=workflow_type,
        matched_triggers=trigger_list,
        matched_actions=action_list,
        trigger_names=[t.name for t in trigger_list],
        action_names=[a.name for a in action_list],
    )


class WorkspaceCatalogMatcher:
    """Builds a CatalogMatchResult from a workspace's mapped definitions."""

    def __init__(self, db: Session):
        self.db = db

    def match(
        self,
        workspace_id: int,
        selected_action_ids: list[int] | None = None,
    ) -> CatalogMatchResult:
        actions = self._workspace_actions(workspace_id)
        triggers = self._workspace_triggers(workspace_id)
        selected = self._actions_by_ids(selected_action_ids or [])
        return build_workspace_match_result(actions, triggers, selected)

    # -- workspace-scoped queries (never global) -------------------------------

    def _workspace_actions(self, workspace_id: int) -> list[ActionDefinition]:
        return (
            self.db.query(ActionDefinition)
            .join(
                WorkflowActionMapping,
                WorkflowActionMapping.matched_action_definition_id == ActionDefinition.id,
            )
            .join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowActionMapping.workflow_knowledge_id,
            )
            .filter(
                WorkflowKnowledge.workspace_id == workspace_id,
                ActionDefinition.active.is_(True),
            )
            .distinct()
            .all()
        )

    def _workspace_triggers(self, workspace_id: int) -> list[TriggerDefinition]:
        return (
            self.db.query(TriggerDefinition)
            .join(
                WorkflowTriggerMapping,
                WorkflowTriggerMapping.matched_trigger_definition_id == TriggerDefinition.id,
            )
            .join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowTriggerMapping.workflow_knowledge_id,
            )
            .filter(
                WorkflowKnowledge.workspace_id == workspace_id,
                TriggerDefinition.active.is_(True),
            )
            .distinct()
            .all()
        )

    def _actions_by_ids(self, ids: list[int]) -> list[ActionDefinition]:
        """Explicitly selected global actions — the only way a non-workspace
        action enters generation."""
        if not ids:
            return []
        return (
            self.db.query(ActionDefinition)
            .filter(
                ActionDefinition.id.in_(ids),
                ActionDefinition.active.is_(True),
            )
            .all()
        )
