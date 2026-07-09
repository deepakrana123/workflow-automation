from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from app.retrieval.models import RetrievalCandidate


class PostgressRetriever:
    def __init__(self, repository: WorkflowRepository):
        self.repository = repository

    def search_actions(self, query: str, limit: int = 20) -> list[RetrievalCandidate]:
        rows = self.repository.search_actions_by_postgress(query, limit)
        return [
            RetrievalCandidate(entity=entity, score=float(rank), source="postgres")
            for entity, rank in rows
        ]

    def search_triggers(self, query: str, limit: int = 20) -> list[RetrievalCandidate]:
        rows = self.repository.search_triggers_by_postgress(query, limit)
        return [
            RetrievalCandidate(entity=entity, score=float(rank), source="postgres")
            for entity, rank in rows
        ]
