"""
BM25 Keyword Retrieval for WorkflowBusinessRule

Provides workspace-scoped semantic keyword retrieval using the BM25 ranking algorithm.
Mirrors KeywordRetriever pattern for Actions and Triggers but handles workspace isolation
and rule-specific text construction.

BM25 indexes are built in-memory from rules in a given workspace. This is appropriate for
workspace-scoped retrieval where workspaces typically have < 10K rules.

For large deployments or when workspaces grow beyond 50K rules, consider:
- Elasticsearch / Opensearch with BM25 backend
- Milvus with BM25 plugin
- PostgreSQL BM25 extension (pgsql-http-bm25)
"""

import re
from typing import Optional

from rank_bm25 import BM25Okapi

from app.knowledge_ingestions.rule_repository import RuleRepository
from app.models.workflow_business_rule import WorkflowBusinessRule
from app.retrieval.models import RetrievalCandidate


class RuleKeywordRetriever:
    """BM25-based keyword retrieval for WorkflowBusinessRule within a workspace."""

    def __init__(
        self, repository: RuleRepository, workspace_id: int, force_refresh: bool = True
    ):
        """
        Initialize the retriever for a specific workspace.

        Args:
            repository: RuleRepository instance
            workspace_id: Workspace to search within
            force_refresh: If True, build BM25 index from current workspace rules
        """
        self.repository = repository
        self.workspace_id = workspace_id
        self.rule_documents: list[WorkflowBusinessRule] = []
        self.rule_index: Optional[BM25Okapi] = None

        if force_refresh:
            self.refresh()

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text: lowercase, remove non-alphanumeric, split on whitespace."""
        text = text.lower()
        text = re.sub(r"[^a-z0-9 ]", " ", text)
        return text.split()

    def _build_rule_text(self, rule: WorkflowBusinessRule) -> str:
        """Construct searchable text from a rule's fields."""
        parts = [
            rule.rule or "",
            rule.condition or "",
            rule.outcome or "",
            rule.responsible_role or "",
            rule.threshold or "",
        ]
        return " ".join(parts)

    def _build_index(
        self, rules: list[WorkflowBusinessRule]
    ) -> Optional[BM25Okapi]:
        """Build BM25 index from rules. Returns None if no rules."""
        if not rules:
            return None

        corpus = [
            self._tokenize(self._build_rule_text(rule))
            for rule in rules
        ]
        return BM25Okapi(corpus)

    def search(
        self, query: str, limit: int = 20
    ) -> list[RetrievalCandidate]:
        """
        Search rules by keyword similarity using BM25.

        Args:
            query: Search query text
            limit: Maximum number of results to return

        Returns:
            List of RetrievalCandidate with entity=WorkflowBusinessRule, score=BM25 score
        """
        if self.rule_index is None:
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

        scores = self.rule_index.get_scores(tokens)
        ranked = sorted(
            zip(self.rule_documents, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            RetrievalCandidate(entity=rule, score=float(score), source="bm25")
            for rule, score in ranked[:limit]
        ]

    def refresh(self) -> None:
        """Rebuild BM25 index from current workspace rules."""
        self.rule_documents = self.repository.get_all_rules_for_workspace(
            self.workspace_id
        )
        self.rule_index = self._build_index(self.rule_documents)
