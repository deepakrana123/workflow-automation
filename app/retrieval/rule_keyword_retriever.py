import re

from rank_bm25 import BM25Okapi

from app.knowledge_ingestions.rule_repository import RuleRepository
from app.retrieval.models import RetrievalCandidate


class RuleKeywordRetriever:
    def __init__(self, repository: RuleRepository, workspace_id: int):
        self.repository = repository
        self.workspace_id = workspace_id

        self._documents: list = []
        self._index: BM25Okapi | None = None

        self.refresh()

    def search(
        self,
        query: str,
        limit: int = 20,
        allowed_ids: set[int] | None = None,
    ) -> list[RetrievalCandidate]:
        """Search the BM25 index.

        allowed_ids — when provided, only rules whose id is in this set
        are scored. The BM25 corpus is pre-built from the full workspace
        at refresh() time; we restrict here by masking out disallowed rows
        BEFORE scoring so BM25 term statistics stay stable and we never
        discard results after the fact.
        """
        if self._index is None:
            return []

        # Build a restricted (document, original_index) list if filter given
        if allowed_ids is not None:
            filtered_pairs = [
                (i, doc) for i, doc in enumerate(self._documents)
                if doc.id in allowed_ids
            ]
            if not filtered_pairs:
                return []
            # Score only the tokens of the filtered subset using the full index
            tokens = self._tokenize(query)
            all_scores = self._index.get_scores(tokens)
            ranked = sorted(
                [(self._documents[i], all_scores[i]) for i, _ in filtered_pairs],
                key=lambda x: x[1],
                reverse=True,
            )
        else:
            tokens = self._tokenize(query)
            scores = self._index.get_scores(tokens)
            ranked = sorted(
                zip(self._documents, scores),
                key=lambda x: x[1],
                reverse=True,
            )

        return [
            RetrievalCandidate(entity=rule, score=float(score), source="bm25")
            for rule, score in ranked[:limit]
            if score > 0.001
        ]

    def refresh(self) -> None:
        self._documents = self.repository.get_all_rules_for_workspace(
            self.workspace_id
        )
        self._index = self._build_index(self._documents)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        text = text.lower()
        text = re.sub(r"[^a-z0-9 ]", " ", text)
        return text.split()

    def _build_index(self, rules: list) -> BM25Okapi | None:
        if not rules:
            return None

        corpus = [
            self._tokenize(
                f"{r.rule or ''} "
                f"{r.condition or ''} "
                f"{r.outcome or ''} "
                f"{r.responsible_role or ''} "
                f"{r.threshold or ''}"
            )
            for r in rules
        ]

        return BM25Okapi(corpus)
