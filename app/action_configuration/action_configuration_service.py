"""
app/action_configuration/action_configuration_service.py

Initialisation service — seeds default ActionConfiguration rows for a
newly-ingested workflow (execution_type=python, handler from catalog).

For user-facing CRUD (update, activate, deactivate) see:
  app/action_configuration/management_service.py
"""

from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from app.repositories.action_configuration_repository import ActionConfigurationRepository
from app.models.action_configurations_model import ActionConfiguration


class ActionConfigurationService:

    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        configuration_repository: ActionConfigurationRepository,
    ):
        self.workflow_repository      = workflow_repository
        self.configuration_repository = configuration_repository

    def initialize_default_configurations(self, workflow_knowledge_id: int) -> None:
        """
        Create a default python ActionConfiguration for every mapped action
        in a workflow. Skips actions that have no matched_action_definition_id.
        """
        actions = self.workflow_repository.get_workflow_actions(workflow_knowledge_id)
        for action in actions:
            if action.matched_action_definition_id is None:
                continue
            configuration = ActionConfiguration(
                workflow_knowledge_id    = workflow_knowledge_id,
                action_definition_id     = action.matched_action_definition_id,
                execution_type           = "python",
                workspace_integration_id = None,
                configuration            = {},
                version                  = 1,
                active                   = True,
            )
            self.configuration_repository.create(configuration)

    def get_active_configuration(
        self,
        workflow_knowledge_id: int,
        action_definition_id: int,
    ) -> ActionConfiguration | None:
        return self.configuration_repository.get_active_configuration(
            workflow_knowledge_id=workflow_knowledge_id,
            action_definition_id=action_definition_id,
        )

    def update_configuration(
        self,
        configuration: ActionConfiguration,
    ) -> None:
        configuration.version += 1
        self.configuration_repository.update(configuration)
