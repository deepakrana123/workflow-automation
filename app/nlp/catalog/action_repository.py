"""
app/nlp/catalog/action_repository.py

Repository for ActionDefinition data access.
"""

from sqlalchemy.orm import Session
from app.models.action_definitions import ActionDefinition


class ActionDefinitionRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_active(self) -> list[ActionDefinition]:
        return (
            self.db.query(ActionDefinition)
            .filter(ActionDefinition.active.is_(True))
            .all()
        )

    def get_by_id(self, action_id: int) -> ActionDefinition | None:
        return (
            self.db.query(ActionDefinition)
            .filter(ActionDefinition.id == action_id)
            .first()
        )

    def get_by_name(self, name: str) -> ActionDefinition | None:
        return (
            self.db.query(ActionDefinition)
            .filter(ActionDefinition.name == name)
            .first()
        )
