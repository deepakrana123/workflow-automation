from app.knowledge_ingestions.workflow_repository import WorkflowRepository
import re
from rank_bm25 import BM25Okapi
from app.retrieval.models import RetrievalCandidate


class KeywordRetriever:
    def __init__(self, repository: WorkflowRepository):
        self.repository = repository
        self.action_documents: list = []
        self.action_index: BM25Okapi | None = None
        self.trigger_documents: list = []
        self.trigger_index: BM25Okapi | None = None
        self.refresh()

    def _tokenize(self, text: str) -> list[str]:
        text = text.lower()
        text = re.sub(r"[^a-z0-9 ]", " ", text)
        return text.split()

    def _build_index(self, objects) -> BM25Okapi | None:
        if not objects:
            return None
        corpus = [self._tokenize(f"{a.name} {a.description or ''}") for a in objects]
        return BM25Okapi(corpus)

    def search_actions(self, query: str, limit: int = 20) -> list[RetrievalCandidate]:
        if self.action_index is None:
            return []
        tokens = self._tokenize(query)
        scores = self.action_index.get_scores(tokens)
        ranked = sorted(
            zip(self.action_documents, scores),
            key=lambda x: x[1],
            reverse=True,
        )
        return [
            RetrievalCandidate(entity=action, score=float(score), source="bm25")
            for action, score in ranked[:limit]
        ]

    def search_triggers(self, query: str, limit: int = 20) -> list[RetrievalCandidate]:
        if self.trigger_index is None:
            return []
        tokens = self._tokenize(query)
        scores = self.trigger_index.get_scores(tokens)
        ranked = sorted(
            zip(self.trigger_documents, scores),
            key=lambda x: x[1],
            reverse=True,
        )
        return [
            RetrievalCandidate(entity=trigger, score=float(score), source="bm25")
            for trigger, score in ranked[:limit]
        ]

    def refresh(self):
        self.action_documents = self.repository.get_all_active_actions()
        self.action_index = self._build_index(self.action_documents)
        self.trigger_documents = self.repository.get_all_active_triggers()
        self.trigger_index = self._build_index(self.trigger_documents)
