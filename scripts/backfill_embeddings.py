from app.db.session import SessionLocal
from app.semantic.embedding_service import EmbeddingService
from app.semantic.vector_repository import VectorRepository
from app.models.action_definitions import ActionDefinition
from app.models.trigger_definitions import TriggerDefinition

db = SessionLocal()

embedding_service = EmbeddingService()
repository = VectorRepository()

triggers = db.query(TriggerDefinition).all()

print(f"Found {len(triggers)} triggers")

for trigger in triggers:
    text = embedding_service.build_trigger_text(trigger)
    vector = embedding_service.generate_embedding(text)

    repository.update_trigger_embedding(
        db,
        trigger.id,
        vector
    )

actions = db.query(ActionDefinition).all()

print(f"Found {len(actions)} actions")

for action in actions:
    text = embedding_service.build_action_text(action)

    vector = embedding_service.generate_embedding(text)

    repository.update_action_embedding(
        db,
        action.id,
        vector
    )

db.commit()

print("Backfill completed")

db.close()