from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from app.retrieval.models import RetrievalCandidate


class VectorRetriever:
    def __init__(self, repository: WorkflowRepository):
        self.repository = repository

    def search_actions(self, embedding, limit: int = 20) -> list[RetrievalCandidate]:
        rows = self.repository.search_actions_by_embedding(embedding, limit=limit)
        return [
            RetrievalCandidate(entity=entity, score=float(distance), source="vector")
            for entity, distance in rows
        ]

    def search_triggers(self, embedding, limit: int = 20) -> list[RetrievalCandidate]:
        rows = self.repository.search_triggers_by_embedding(embedding, limit=limit)
        return [
            RetrievalCandidate(entity=entity, score=float(distance), source="vector")
            for entity, distance in rows
        ]
