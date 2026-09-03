"""
app/execution/runtime/config_resolver.py

Resolves the ActionDefinition for a given action name scoped to a workspace.

Resolution path:
  action_name + workspace_id
    → WorkflowActionMapping (matched_action_definition_id)
       JOIN WorkflowKnowledge (workspace_id filter)
    → ActionDefinition

Falls back to a global lookup by action name when workspace_id is None
(e.g. workflows generated outside any workspace).

Returns the ActionDefinition ORM object, or None if not found.
Never raises — logs a warning and returns None on any DB error.
"""

from sqlalchemy.orm import Session

from app.models.action_definitions import ActionDefinition
from app.core.logger import logger


def resolve_action_definition(
    db: Session,
    action_name: str,
    workspace_id: int | None,
) -> ActionDefinition | None:
    """
    Load the ActionDefinition for an action name.

    Resolution order:
      1. If workspace_id is available:
         workspace-scoped lookup via WorkflowActionMapping → WorkflowKnowledge.
      2. Fallback: global lookup by action name (active=True).

    Returns ActionDefinition if found, None otherwise.
    """
    try:
        if workspace_id is not None:
            from app.knowledge_ingestions.workflow_repository import WorkflowRepository
            repo = WorkflowRepository(db)
            action_def = repo.get_action_definition_for_action(
                workspace_id=workspace_id,
                action_name=action_name,
            )
            if action_def is not None:
                return action_def

        # Fallback — global catalog lookup
        return (
            db.query(ActionDefinition)
            .filter(
                ActionDefinition.name == action_name,
                ActionDefinition.active.is_(True),
            )
            .first()
        )

    except Exception as exc:
        logger.warning(
            "config_resolver_lookup_failed",
            extra={"extra_data": {
                "action_name": action_name,
                "workspace_id": workspace_id,
                "error": str(exc),
            }},
        )
        return None
