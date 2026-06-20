from sqlalchemy import text
from app.models.trigger_definitions import TriggerDefinition
from app.models.action_definitions import ActionDefinition


class SemanticRepository:

    DISTANCE_THRESHOLD = 0.30

    def search_triggers(self, db, embedding, limit=5):
        query = text("""
            SELECT id, embedding <=> CAST(:embedding AS vector) AS distance
            FROM trigger_definitions
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)

        rows = db.execute(query, {
            "embedding": str(embedding),
            "limit": limit,
        }).fetchall()

        # Filter by threshold and return full ORM objects
        ids = [row.id for row in rows if row.distance < self.DISTANCE_THRESHOLD]
        if not ids:
            return []

        return (
            db.query(TriggerDefinition)
            .filter(TriggerDefinition.id.in_(ids))
            .filter(TriggerDefinition.active == True)
            .all()
        )

    def search_actions(self, db, embedding, limit=5):
        query = text("""
            SELECT id, embedding <=> CAST(:embedding AS vector) AS distance
            FROM action_definitions
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)

        rows = db.execute(query, {
            "embedding": str(embedding),
            "limit": limit,
        }).fetchall()

        ids = [row.id for row in rows if row.distance < self.DISTANCE_THRESHOLD]
        if not ids:
            return []

        return (
            db.query(ActionDefinition)
            .filter(ActionDefinition.id.in_(ids))
            .filter(ActionDefinition.active == True)
            .all()
        )
