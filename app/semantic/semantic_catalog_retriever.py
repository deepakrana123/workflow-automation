from app.semantic.embedding_service import EmbeddingService
from app.semantic.semantic_repository import SemanticRepository


class SemanticCatalogRetriever:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.repository = SemanticRepository()

    def retrieve(
        self, db, user_request: str, trigger_limit: int = 3, action_limit: int = 5
    ):
        embedding = self.embedding_service.generate_embedding(user_request)
        triggers = self.repository.search_triggers(db, embedding, trigger_limit)
        actions = self.repository.search_actions(db, embedding, action_limit)
        return triggers, actions
