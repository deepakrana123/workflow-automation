"""
app/execution/runtime/config_resolver.py

Resolves ActionConfiguration for a given action name and workflow context.

Single authoritative implementation — used by both StepExecutor and RetryExecutor
so the lookup logic is never duplicated.
"""

from app.models.action_definitions import ActionDefinition
from app.repositories.action_configuration_repository import ActionConfigurationRepository
from app.models.action_configurations_model import ActionConfiguration
from app.core.logger import logger
from sqlalchemy.orm import Session


def resolve_action_configuration(
    db: Session,
    action_name: str,
    workflow_knowledge_id: int | None,
    config_repo: ActionConfigurationRepository | None = None,
) -> tuple[ActionConfiguration | None, str]:
    """
    Load the active ActionConfiguration for an action.

    Resolution order:
      1. If workflow_knowledge_id is available:
         exact lookup by (workflow_knowledge_id, action_definition_id)
      2. Fallback: latest active config by action_definition_id only.

    Returns:
        (ActionConfiguration, execution_type) if found.
        (None, "python") if the action definition or config does not exist.

    Never raises — logs a warning and returns (None, "python") on any DB error
    so the caller can decide how to handle the missing config.
    """
    try:
        action_def = (
            db.query(ActionDefinition)
            .filter(
                ActionDefinition.name == action_name,
                ActionDefinition.active.is_(True),
            )
            .first()
        )

        if action_def is None:
            return None, "python"

        repo = config_repo or ActionConfigurationRepository(db)

        if workflow_knowledge_id is not None:
            config = repo.get_active_configuration(
                workflow_knowledge_id=workflow_knowledge_id,
                action_definition_id=action_def.id,
            )
        else:
            config = repo.get_by_action_definition(
                action_definition_id=action_def.id,
            )

        if config is None:
            return None, "python"

        return config, config.execution_type or "python"

    except Exception as exc:
        logger.warning(
            "config_resolver_lookup_failed",
            extra={"extra_data": {
                "action_name":           action_name,
                "workflow_knowledge_id": workflow_knowledge_id,
                "error":                 str(exc),
            }},
        )
        return None, "python"
