from sqlalchemy.orm import Session
from app.models.action_configurations_model import ActionConfiguration


class ActionConfigurationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, configuration: ActionConfiguration) -> ActionConfiguration:
        self.db.add(configuration)
        self.db.commit()
        self.db.refresh(configuration)
        return configuration

    def update(self, configuration: ActionConfiguration) -> ActionConfiguration:
        self.db.commit()
        self.db.refresh(configuration)
        return configuration

    def get_by_workflow(self, workflow_knowledge_id: int) -> list[ActionConfiguration]:
        return (
            self.db.query(ActionConfiguration)
            .filter(ActionConfiguration.workflow_knowledge_id == workflow_knowledge_id)
            .all()
        )

    def get_active_configuration(
        self,
        workflow_knowledge_id: int,
        action_definition_id: int,
    ) -> ActionConfiguration | None:
        # Bug fix: .first() was inside the filter chain — moved outside correctly
        return (
            self.db.query(ActionConfiguration)
            .filter(
                ActionConfiguration.workflow_knowledge_id == workflow_knowledge_id,
                ActionConfiguration.action_definition_id == action_definition_id,
                ActionConfiguration.active.is_(True),
            )
            .order_by(ActionConfiguration.version.desc())
            .first()
        )
