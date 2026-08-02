"""
app/nlp/catalog/trigger_repository.py

Repository for TriggerDefinition data access.
"""

from sqlalchemy.orm import Session
from app.models.trigger_definitions import TriggerDefinition


class TriggerDefinitionRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_active(self) -> list[TriggerDefinition]:
        return (
            self.db.query(TriggerDefinition)
            .filter(TriggerDefinition.active.is_(True))
            .all()
        )

    def get_by_id(self, trigger_id: int) -> TriggerDefinition | None:
        return (
            self.db.query(TriggerDefinition)
            .filter(TriggerDefinition.id == trigger_id)
            .first()
        )

    def get_by_name(self, name: str) -> TriggerDefinition | None:
        return (
            self.db.query(TriggerDefinition)
            .filter(TriggerDefinition.name == name)
            .first()
        )
