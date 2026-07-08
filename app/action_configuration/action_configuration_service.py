from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from app.repositories.action_configuration_repository import ActionConfigurationRepository
from app.models.action_configurations_model import ActionConfiguration


class ActionConfigurationService:
    """
    Manages ActionConfiguration lifecycle.

    Responsibilities:
    - Initialize default configurations after embedding mapping
    - Retrieve active configuration for dispatcher lookup
    - Support future versioning without redesign

    Current execution_type support: python
    Future execution_types: http, mcp, ai_agent, human_task
    """

    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        configuration_repository: ActionConfigurationRepository,
    ):
        self.workflow_repository = workflow_repository
        self.configuration_repository = configuration_repository

    def initialize_workflow(self, workflow_knowledge_id: int) -> None:
        """
        Create default ActionConfiguration for each mapped action in the workflow.
        Skips actions that have no matched_action_definition_id (unmapped).
        Sets execution_type=python and handler from action_definition.handler_name.
        """
        actions = self.workflow_repository.get_workflow_actions(workflow_knowledge_id)

        for action in actions:
            if action.matched_action_definition_id is None:
                continue

            # Read handler_name from the matched action_definition
            handler_name = None
            if action.action_definition and action.action_definition.handler_name:
                handler_name = action.action_definition.handler_name
            elif action.action_definition:
                # Fallback: use canonical name as handler
                handler_name = action.action_definition.name

            configuration = ActionConfiguration(
                workflow_knowledge_id=workflow_knowledge_id,
                action_definition_id=action.matched_action_definition_id,
                version=1,
                configuration={
                    "execution_type": "python",
                    "handler": handler_name or "",
                },
                active=True,
            )
            self.configuration_repository.create(configuration)

    def get_active_configuration(
        self,
        workflow_knowledge_id: int,
        action_definition_id: int,
    ) -> ActionConfiguration | None:
        """Retrieve the active configuration for a specific action in a workflow."""
        return self.configuration_repository.get_active_configuration(
            workflow_knowledge_id=workflow_knowledge_id,
            action_definition_id=action_definition_id,
        )

    def update_configuration(
        self,
        configuration: ActionConfiguration,
        new_config: dict,
    ) -> ActionConfiguration:
        """Update execution configuration. Creates a new version."""
        configuration.configuration = new_config
        configuration.version += 1
        return self.configuration_repository.update(configuration)
