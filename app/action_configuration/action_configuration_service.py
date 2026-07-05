from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from app.repositories.action_configuration_repository import (
    ActionConfigurationRepository,
)
from app.models.action_configurations_model import ActionConfiguration


class ActionConfigurationServie:
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        configuration_repository: ActionConfigurationRepository,
    ):
        self.workflow_repository = workflow_repository
        self.configuration_repository = configuration_repository

    def initialize_workflow(self, workflow_knowledge_id: int):
        actions = self.workflow_repository.get_workflow_actions(workflow_knowledge_id)

        for action in actions:
            if action.matched_action_definition_id is None:
                continue

            configuration = ActionConfiguration(
                workflow_knowledge_id=workflow_knowledge_id,
                action_definition_id=action.matched_action_definition_id,
                version=1,
                configuration={},
                active=True,
            )
            self.configuration_repository.create(configuration)
