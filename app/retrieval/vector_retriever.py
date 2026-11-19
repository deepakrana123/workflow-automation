from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from app.retrieval.models import RetrievalCandidate
from app.core.logger import logger
from sqlalchemy import func


class VectorRetriever:
    def __init__(self, repository: WorkflowRepository):
        self.repository = repository

    def search_actions(self, embedding, limit: int = 20) -> list[RetrievalCandidate]:
        # Phase 6: Log NULL embedding statistics
        null_count = self.repository.count_null_action_embeddings()
        if null_count > 0:
            logger.warning(
                "vector_retrieval_null_embeddings",
                extra={
                    "extra_data": {
                        "entity_type": "action",
                        "null_count": null_count,
                    }
                },
            )

        rows = self.repository.search_actions_by_embedding(embedding, limit=limit)
        return [
            RetrievalCandidate(entity=entity, score=float(distance), source="vector")
            for entity, distance in rows
        ]

    def search_triggers(self, embedding, limit: int = 20) -> list[RetrievalCandidate]:
        # Phase 6: Log NULL embedding statistics
        null_count = self.repository.count_null_trigger_embeddings()
        if null_count > 0:
            logger.warning(
                "vector_retrieval_null_embeddings",
                extra={
                    "extra_data": {
                        "entity_type": "trigger",
                        "null_count": null_count,
                    }
                },
            )

        rows = self.repository.search_triggers_by_embedding(embedding, limit=limit)
        return [
            RetrievalCandidate(entity=entity, score=float(distance), source="vector")
            for entity, distance in rows
        ]
