"""
app/execution/runtime/config_resolver.py

Resolves the ActionDefinition for a given action name scoped to a workspace.

Resolution path:
  1. workspace_id provided:
     WorkflowActionMapping.action_name == action_name
       + WorkflowKnowledge.workspace_id filter
     → synthesize ActionDefinition from snapshot (handles both Mode A and
       Mode B workspace-local actions correctly)
     → fall through to ActionDefinition row if snapshot has no execution_template

  2. workspace_id is None (globally-generated workflow):
     Direct ActionDefinition.name lookup (global catalog fallback).

  3. Last resort (handler map):
     If DB has no row at all but the action name is registered in
     ACTION_HANDLER_MAP, synthesize a minimal ActionDefinition so the
     PythonExecutor Tier-1 path can still run.

Returns the ActionDefinition ORM object (or a synthetic equivalent), or None.
Never raises.
"""

from sqlalchemy.orm import Session

from app.models.action_definitions import ActionDefinition
from app.core.logger import logger


def resolve_action_definition(
    db: Session,
    action_name: str,
    workspace_id: int | None,
) -> ActionDefinition | None:
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

        # Global catalog fallback (non-workspace workflows or workspace miss)
        action_def = (
            db.query(ActionDefinition)
            .filter(
                ActionDefinition.name == action_name,
                ActionDefinition.active.is_(True),
            )
            .first()
        )
        if action_def is not None:
            return action_def

        # Last resort: action is in the handler map but has no DB row.
        # Synthesize a minimal ActionDefinition so Tier-1 execution proceeds.
        from app.execution.python.action_handler_registry import ACTION_HANDLER_MAP
        if action_name in ACTION_HANDLER_MAP:
            synthetic = ActionDefinition()
            synthetic.id               = 0
            synthetic.name             = action_name
            synthetic.display_name     = action_name.replace("_", " ").title()
            synthetic.active           = True
            synthetic.workflow_type    = "finance"
            synthetic.aliases          = []
            synthetic.input_schema     = None
            synthetic.output_schema    = None
            synthetic.execution_template = {
                "execution_type": "python",
                "configuration":  {"handler": action_name},
            }
            return synthetic

        return None

    except Exception as exc:
        logger.warning(
            "config_resolver_lookup_failed",
            extra={"extra_data": {
                "action_name":  action_name,
                "workspace_id": workspace_id,
                "error":        str(exc),
            }},
        )
        return None
