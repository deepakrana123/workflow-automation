from app.knowledge_ingestions.rule_repository import RuleRepository
from app.retrieval.models import RetrievalCandidate


class RulePostgresRetriever:
    def __init__(self, repository: RuleRepository, workspace_id: int):
        self.repository = repository
        self.workspace_id = workspace_id

    def search(
        self,
        query: str,
        limit: int = 20,
        allowed_ids: set[int] | None = None,
    ) -> list[RetrievalCandidate]:
        """Full-text search over rules.

        allowed_ids — when provided, the DB query adds an IN clause so only
        those rule IDs are considered. The filter happens in SQL, not after
        results are returned.
        """
        rows = self.repository.search_by_fts(
            self.workspace_id, query, limit, allowed_ids=allowed_ids
        )
        return [
            RetrievalCandidate(entity=rule, score=float(rank), source="postgres")
            for rule, rank in rows
        ]
