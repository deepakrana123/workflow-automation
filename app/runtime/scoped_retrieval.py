"""
app/runtime/scoped_retrieval.py

ScopedRetrievalService — wraps the existing RetrievalPipeline with context-
aware RBAC filtering.

Key design rule: retrieval never grants permission.
  - The pipeline retrieves semantically relevant candidates.
  - RBAC filtering is applied AFTER retrieval to produce the allowed set.
  - Retrieval diagnostics (vector_rank, bm25_rank, postgres_rank, rrf_score)
    are preserved for every candidate — including unauthorized ones (internally).
  - The caller decides what to expose vs. what to suppress.

The existing RetrievalPipeline is NOT modified. This service adapts it.

The evaluation CLI continues to call RetrievalPipeline directly and is
unaffected by this wrapper.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from app.retrieval.pipeline import RetrievalPipeline
from app.retrieval.models import RankedCandidate
from app.runtime.context import RetrievalContext
from app.core.logger import logger


@dataclass
class ScoredCandidate:
    """A retrieval candidate with authorization result attached."""

    action_id: int
    action_name: str
    display_name: str
    description: Optional[str]
    workflow_type: str

    # Retrieval scores
    vector_rank:   Optional[int]
    bm25_rank:     Optional[int]
    postgres_rank: Optional[int]
    rrf_score:     float

    # Authorization result
    authorized: bool
    rejection_reason: Optional[str]  # None when authorized

    final_rank: Optional[int] = None  # Set after filtering and re-ranking


@dataclass
class ScopedRetrievalResult:
    """Full result of a scoped retrieval query."""

    query: str
    total_retrieved: int
    total_authorized: int

    # Authorized candidates only — ordered by final_rank
    candidates: list[ScoredCandidate] = field(default_factory=list)

    # All retrieved candidates including unauthorized (for admin diagnostics)
    diagnostics: list[ScoredCandidate] = field(default_factory=list)

    selected_action_id: Optional[int] = None
    selected_action_name: Optional[str] = None


class ScopedRetrievalService:
    """
    Context-aware retrieval adapter over the existing RetrievalPipeline.

    Usage:
        svc = ScopedRetrievalService(pipeline, db)
        result = svc.retrieve(query="apply interest", ctx=ctx, top_k=10)
    """

    def __init__(self, pipeline: RetrievalPipeline, db: Session, embedder=None):
        """
        Args:
            pipeline:  Existing RetrievalPipeline instance.
            db:        SQLAlchemy session.
            embedder:  Optional callable(str) → list[float]. If None, the service
                       falls back to keyword-only retrieval (no vector component).
        """
        self._pipeline = pipeline
        self._db = db
        self._embedder = embedder

    def retrieve(
        self,
        query: str,
        ctx: RetrievalContext,
        top_k: int = 10,
        include_unauthorized_diagnostics: bool = False,
    ) -> ScopedRetrievalResult:
        """
        Run the full retrieval pipeline, then apply RBAC scope filtering.

        Args:
            query:      Natural-language query string.
            ctx:        RetrievalContext with resolved RBAC (allowed_action_ids).
            top_k:      Maximum number of authorized candidates to return.
            include_unauthorized_diagnostics:
                        If True, include filtered-out candidates in .diagnostics
                        (for admin/developer observability only — never expose to
                        regular users).

        Returns:
            ScopedRetrievalResult with candidates ordered by rrf_score.
        """
        # Embed the query if an embedder is available
        embedding: list[float] | None = None
        if self._embedder:
            try:
                embedding = self._embedder(query)
            except Exception as exc:
                logger.warning(
                    "scoped_retrieval_embed_failed",
                    extra={"extra_data": {"error": str(exc)}},
                )

        # Run retrieval
        try:
            if embedding is not None:
                raw_candidates: list[RankedCandidate] = self._pipeline.retrieve_actions(
                    query, embedding, limit=max(top_k * 5, 50)
                )
            else:
                # Fall back to keyword + postgres only (no vector component)
                raw_candidates = self._pipeline.retrieve_actions(
                    query, [], limit=max(top_k * 5, 50)
                )
        except Exception as exc:
            logger.error(
                "scoped_retrieval_pipeline_failed",
                extra={"extra_data": {"query": query, "error": str(exc)}},
            )
            return ScopedRetrievalResult(
                query=query,
                total_retrieved=0,
                total_authorized=0,
            )

        # Build allowed_action_ids set — treat None as "all allowed" for global search
        allowed_ids: set[int] | None = ctx.allowed_action_ids

        authorized: list[ScoredCandidate] = []
        diagnostics: list[ScoredCandidate] = []

        for rank_idx, rc in enumerate(raw_candidates):
            action = rc.entity
            action_id = action.id

            # RBAC filter
            if allowed_ids is not None and action_id not in allowed_ids:
                sc = ScoredCandidate(
                    action_id=action_id,
                    action_name=action.name,
                    display_name=action.display_name or action.name,
                    description=action.description,
                    workflow_type=action.workflow_type,
                    vector_rank=rc.vector_rank,
                    bm25_rank=rc.bm25_rank,
                    postgres_rank=rc.postgres_rank,
                    rrf_score=rc.rrf_score,
                    authorized=False,
                    rejection_reason="ACTION_NOT_IN_ALLOWED_SCOPE",
                )
                if include_unauthorized_diagnostics:
                    diagnostics.append(sc)
                continue

            sc = ScoredCandidate(
                action_id=action_id,
                action_name=action.name,
                display_name=action.display_name or action.name,
                description=action.description,
                workflow_type=action.workflow_type,
                vector_rank=rc.vector_rank,
                bm25_rank=rc.bm25_rank,
                postgres_rank=rc.postgres_rank,
                rrf_score=rc.rrf_score,
                authorized=True,
                rejection_reason=None,
            )
            authorized.append(sc)
            if include_unauthorized_diagnostics:
                diagnostics.append(sc)

        # Assign final_rank to authorized candidates (preserve rrf_score order)
        authorized = authorized[:top_k]
        for i, sc in enumerate(authorized, start=1):
            sc.final_rank = i

        selected_id = authorized[0].action_id if authorized else None
        selected_name = authorized[0].action_name if authorized else None

        return ScopedRetrievalResult(
            query=query,
            total_retrieved=len(raw_candidates),
            total_authorized=len(authorized),
            candidates=authorized,
            diagnostics=diagnostics if include_unauthorized_diagnostics else [],
            selected_action_id=selected_id,
            selected_action_name=selected_name,
        )
