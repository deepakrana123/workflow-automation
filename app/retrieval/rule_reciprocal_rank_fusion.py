"""
Reciprocal Rank Fusion (RRF) for WorkflowBusinessRule Retrieval

Combines results from three independent retrieval channels using the standard RRF formula:

    RRF_score(d) = Σ 1 / (k + rank_i(d))

Where:
- d is a WorkflowBusinessRule
- rank_i(d) is its rank (position) in channel i (1-indexed)
- k is a constant (default 60) for decay; prevents dominance by top-ranked documents
- Only channels in which d appears contribute to the sum

Requirements satisfied:
1. Uses ranks (not raw scores) from each channel for fair comparison
2. Deduplicates by rule.id
3. Preserves individual channel ranks and scores
4. Returns fused score
5. Supports configurable final top_k
6. Handles missing/empty channels gracefully
7. Returns empty list if all channels empty
8. Deterministic tie-breaking: by fused_score DESC, then rule.id ASC
9. Preserves all rule content and provenance
10. Enforces workspace/tenant isolation at fusion layer
"""

from dataclasses import dataclass, field
from typing import Optional, Any

from app.models.workflow_business_rule import WorkflowBusinessRule
from app.models.workflow_knowledge import WorkflowKnowledge
from app.retrieval.models import RetrievalCandidate
from sqlalchemy.orm import Session


@dataclass
class FusedRetrievalResult:
    """
    Result of RRF fusion across multiple retrieval channels.

    Preserves individual channel rankings and original scores alongside
    the final fused RRF score.
    """

    rule: WorkflowBusinessRule
    
    # Fused rank fusion score
    rrf_score: float

    # Individual channel ranks (1-indexed, or None if not retrieved by channel)
    vector_rank: Optional[int] = None
    vector_score: Optional[float] = None
    
    bm25_rank: Optional[int] = None
    bm25_score: Optional[float] = None
    
    postgres_rank: Optional[int] = None
    postgres_score: Optional[float] = None

    # Debugging: how many channels retrieved this rule
    retrieval_channels: int = field(default=0, init=False)

    def __post_init__(self):
        """Calculate retrieval_channels count."""
        count = 0
        if self.vector_rank is not None:
            count += 1
        if self.bm25_rank is not None:
            count += 1
        if self.postgres_rank is not None:
            count += 1
        object.__setattr__(self, "retrieval_channels", count)


class RuleReciprocalRankFusion:
    """
    Fuse results from vector, BM25, and PostgreSQL FTS retrieval channels
    using Reciprocal Rank Fusion.

    Usage:
        fusion = RuleReciprocalRankFusion(session, workspace_id, tenant_id=None)
        fused = fusion.fuse(
            vector_results=[...],
            bm25_results=[...],
            postgres_results=[...],
            top_k=20,
        )
    """

    def __init__(
        self,
        session: Session,
        workspace_id: int,
        tenant_id: Optional[int] = None,
        k: int = 60,
    ):
        """
        Initialize the fusion engine.

        Args:
            session: SQLAlchemy session for workspace/tenant validation
            workspace_id: Workspace to validate membership
            tenant_id: Optional tenant_id to validate workspace ownership
            k: RRF decay constant (default 60)
        """
        self.session = session
        self.workspace_id = workspace_id
        self.tenant_id = tenant_id
        self.k = k

        # Validate workspace exists and (if tenant_id provided) belongs to tenant
        self._validate_workspace()

    def _validate_workspace(self) -> None:
        """Verify workspace exists and (if tenant_id supplied) belongs to tenant."""
        from app.models.workspace import Workspace

        ws = self.session.query(Workspace).filter_by(id=self.workspace_id).first()
        if ws is None:
            raise ValueError(f"Workspace {self.workspace_id} not found")

        if self.tenant_id is not None and ws.tenant_id != self.tenant_id:
            raise ValueError(
                f"Workspace {self.workspace_id} does not belong to tenant {self.tenant_id}"
            )

    def fuse(
        self,
        vector_results: list[RetrievalCandidate],
        bm25_results: list[RetrievalCandidate],
        postgres_results: list[RetrievalCandidate],
        top_k: int = 20,
    ) -> list[FusedRetrievalResult]:
        """
        Fuse results from three retrieval channels using RRF.

        Args:
            vector_results: Results from vector search (source="vector")
            bm25_results: Results from BM25 search (source="bm25")
            postgres_results: Results from PostgreSQL FTS (source="postgres")
            top_k: Maximum number of results to return

        Returns:
            List of FusedRetrievalResult sorted by RRF score (descending),
            then by rule.id (ascending) for deterministic tie-breaking.
            Empty list if all input channels are empty.

        Raises:
            ValueError: If any result belongs to a different workspace
        """
        # Build index: rule.id -> (rank, source, score)
        rule_index: dict[int, dict] = {}

        # Process vector results
        for rank, candidate in enumerate(vector_results, start=1):
            self._validate_result_workspace(candidate)
            rule_id = candidate.entity.id
            if rule_id not in rule_index:
                rule_index[rule_id] = {"rule": candidate.entity}
            rule_index[rule_id]["vector_rank"] = rank
            rule_index[rule_id]["vector_score"] = candidate.score

        # Process BM25 results
        for rank, candidate in enumerate(bm25_results, start=1):
            self._validate_result_workspace(candidate)
            rule_id = candidate.entity.id
            if rule_id not in rule_index:
                rule_index[rule_id] = {"rule": candidate.entity}
            rule_index[rule_id]["bm25_rank"] = rank
            rule_index[rule_id]["bm25_score"] = candidate.score

        # Process Postgres results
        for rank, candidate in enumerate(postgres_results, start=1):
            self._validate_result_workspace(candidate)
            rule_id = candidate.entity.id
            if rule_id not in rule_index:
                rule_index[rule_id] = {"rule": candidate.entity}
            rule_index[rule_id]["postgres_rank"] = rank
            rule_index[rule_id]["postgres_score"] = candidate.score

        if not rule_index:
            return []

        # Calculate RRF scores
        fused_results = []
        for rule_id, data in rule_index.items():
            rrf_score = 0.0

            if "vector_rank" in data:
                rrf_score += 1.0 / (self.k + data["vector_rank"])

            if "bm25_rank" in data:
                rrf_score += 1.0 / (self.k + data["bm25_rank"])

            if "postgres_rank" in data:
                rrf_score += 1.0 / (self.k + data["postgres_rank"])

            result = FusedRetrievalResult(
                rule=data["rule"],
                rrf_score=rrf_score,
                vector_rank=data.get("vector_rank"),
                vector_score=data.get("vector_score"),
                bm25_rank=data.get("bm25_rank"),
                bm25_score=data.get("bm25_score"),
                postgres_rank=data.get("postgres_rank"),
                postgres_score=data.get("postgres_score"),
            )
            fused_results.append(result)

        # Sort: RRF score descending, then rule.id ascending (deterministic)
        fused_results.sort(key=lambda r: (-r.rrf_score, r.rule.id))

        # Apply top_k limit
        return fused_results[:top_k]

    def _validate_result_workspace(self, candidate: RetrievalCandidate) -> None:
        """
        Verify that a retrieval result belongs to the requested workspace.

        Raises ValueError if rule is in a different workspace.
        """
        rule = candidate.entity
        knowledge = (
            self.session.query(WorkflowKnowledge)
            .filter_by(id=rule.workflow_knowledge_id)
            .first()
        )

        if knowledge is None:
            raise ValueError(
                f"WorkflowKnowledge {rule.workflow_knowledge_id} not found"
            )

        if knowledge.workspace_id != self.workspace_id:
            raise ValueError(
                f"Rule {rule.id} belongs to workspace {knowledge.workspace_id}, "
                f"not {self.workspace_id}"
            )
