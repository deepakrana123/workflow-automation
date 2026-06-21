from sqlalchemy.orm import Session
from app.models.trigger_definitions import TriggerDefinition
from app.models.action_definitions import ActionDefinition


class VectorRepository:
    def update_trigger_embedding(
        self, db: Session, trigger_id: int, embedding: list[float]
    ):
        trigger = (
            db.query(TriggerDefinition)
            .filter(TriggerDefinition.id == trigger_id)
            .first()
        )

        trigger.embedding = embedding

        db.commit()

    def update_action_embedding(
        self, db: Session, action_id: int, embedding: list[float]
    ):
        action = (
            db.query(ActionDefinition).filter(ActionDefinition.id == action_id).first()
        )

        action.embedding = embedding

        db.commit()
