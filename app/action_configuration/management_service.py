"""
app/action_configuration/management_service.py

ActionConfigurationManagementService — user-facing CRUD for ActionConfiguration.

Responsibilities:
  - Retrieve configurations for a workflow
  - Update (create new version, deactivate old)
  - Activate / deactivate specific versions
  - Validate configuration shape against execution_type
  - Never create duplicate active versions for the same
    (workflow_knowledge_id, action_definition_id) pair
"""

from sqlalchemy.orm import Session

from app.models.action_configurations_model import ActionConfiguration
from app.models.workflow_knowledge import WorkflowKnowledge
from app.repositories.action_configuration_repository import ActionConfigurationRepository
from app.workspace_integrations.repository import WorkspaceIntegrationRepository
from app.schemas.action_configuration import ActionConfigurationUpdate
from app.core.logger import logger


# ── Per-execution-type required configuration keys ────────────────────────────
_REQUIRED_KEYS: dict[str, set[str]] = {
    "python": {"handler"},
    "http":   {"endpoint", "method"},
}


class ActionConfigurationManagementService:

    def __init__(
        self,
        db: Session,
        config_repo: ActionConfigurationRepository | None = None,
        wi_repo: WorkspaceIntegrationRepository | None = None,
    ):
        self.db          = db
        self.config_repo = config_repo or ActionConfigurationRepository(db)
        self.wi_repo     = wi_repo or WorkspaceIntegrationRepository(db)

    # ── Read ──────────────────────────────────────────────────────────────────

    def get(self, configuration_id: int) -> ActionConfiguration:
        config = self.config_repo.get_by_id(configuration_id)
        if config is None:
            raise ValueError(f"ActionConfiguration {configuration_id} not found")
        return config

    def list_by_workflow(
        self,
        workflow_knowledge_id: int,
    ) -> list[ActionConfiguration]:
        self._assert_workflow_exists(workflow_knowledge_id)
        return self.config_repo.get_by_workflow(workflow_knowledge_id)

    # ── Update — creates new version, deactivates previous ───────────────────

    def update(
        self,
        configuration_id: int,
        payload: ActionConfigurationUpdate,
    ) -> ActionConfiguration:
        existing = self.get(configuration_id)
        self._validate_payload(payload)

        # Deactivate all current active configs for this action in this workflow
        self._deactivate_all(
            workflow_knowledge_id=existing.workflow_knowledge_id,
            action_definition_id=existing.action_definition_id,
        )

        new_version = ActionConfiguration(
            workflow_knowledge_id    = existing.workflow_knowledge_id,
            action_definition_id     = existing.action_definition_id,
            workspace_integration_id = payload.workspace_integration_id,
            execution_type           = payload.execution_type,
            configuration            = payload.configuration,
            version                  = existing.version + 1,
            active                   = True,
        )
        result = self.config_repo.create(new_version)

        self.db.commit()

        logger.info(
            "action_configuration_updated",
            extra={"extra_data": {
                "workflow_knowledge_id":    result.workflow_knowledge_id,
                "action_definition_id":     result.action_definition_id,
                "new_configuration_id":     result.id,
                "new_version":              result.version,
                "execution_type":           result.execution_type,
            }},
        )
        return result

    # ── Activate ──────────────────────────────────────────────────────────────

    def activate(self, configuration_id: int) -> ActionConfiguration:
        config = self.get(configuration_id)
        if config.active:
            return config

        # Deactivate any other active version for the same action/workflow
        self._deactivate_all(
            workflow_knowledge_id=config.workflow_knowledge_id,
            action_definition_id=config.action_definition_id,
        )

        config.active = True
        self.db.commit()
        self.db.refresh(config)

        logger.info(
            "action_configuration_activated",
            extra={"extra_data": {
                "configuration_id":      configuration_id,
                "workflow_knowledge_id": config.workflow_knowledge_id,
                "action_definition_id":  config.action_definition_id,
                "version":               config.version,
            }},
        )
        return config

    # ── Deactivate ────────────────────────────────────────────────────────────

    def deactivate(self, configuration_id: int) -> ActionConfiguration:
        config = self.get(configuration_id)
        if not config.active:
            return config

        config.active = False
        self.db.commit()
        self.db.refresh(config)

        logger.info(
            "action_configuration_deactivated",
            extra={"extra_data": {
                "configuration_id":      configuration_id,
                "workflow_knowledge_id": config.workflow_knowledge_id,
                "action_definition_id":  config.action_definition_id,
                "version":               config.version,
            }},
        )
        return config

    # ── Private helpers ───────────────────────────────────────────────────────

    def _assert_workflow_exists(self, workflow_knowledge_id: int) -> None:
        exists = (
            self.db.query(WorkflowKnowledge)
            .filter(WorkflowKnowledge.id == workflow_knowledge_id)
            .first()
        )
        if not exists:
            raise ValueError(f"WorkflowKnowledge {workflow_knowledge_id} not found")

    def _validate_payload(self, payload: ActionConfigurationUpdate) -> None:
        # Validate workspace_integration_id exists when provided
        if payload.workspace_integration_id is not None:
            wi = self.wi_repo.get_by_id(payload.workspace_integration_id)
            if wi is None:
                raise ValueError(
                    f"WorkspaceIntegration {payload.workspace_integration_id} not found"
                )
            if not wi.active:
                raise ValueError(
                    f"WorkspaceIntegration {payload.workspace_integration_id} is inactive"
                )

        # http execution_type requires a workspace_integration_id
        if payload.execution_type == "http" and payload.workspace_integration_id is None:
            raise ValueError(
                "execution_type='http' requires workspace_integration_id"
            )

        # Validate required configuration keys per execution_type
        required = _REQUIRED_KEYS.get(payload.execution_type, set())
        missing  = required - set(payload.configuration.keys())
        if missing:
            raise ValueError(
                f"configuration missing required keys for "
                f"execution_type='{payload.execution_type}': {sorted(missing)}"
            )

    def _deactivate_all(
        self,
        workflow_knowledge_id: int,
        action_definition_id: int,
    ) -> None:
        """Deactivate all active configs for the given (workflow, action) pair."""
        self.config_repo.deactivate_all(
            workflow_knowledge_id=workflow_knowledge_id,
            action_definition_id=action_definition_id,
        )
