"""
app/runtime/dependencies.py

FastAPI dependency injection for the runtime layer.

The pipeline is built lazily and cached at module level (singleton per process).
The evaluation CLI is NOT affected — it builds its own RetrievalPipeline directly.
"""

from __future__ import annotations

import threading
from typing import Optional

from sqlalchemy.orm import Session

from app.runtime.orchestrator import WorkflowRuntimeOrchestrator
from app.runtime.scoped_retrieval import ScopedRetrievalService
from app.core.logger import logger

_pipeline_lock = threading.Lock()
_pipeline_singleton: Optional[object] = None
_embedder_singleton: Optional[object] = None


def _build_pipeline() -> None:
    global _pipeline_singleton, _embedder_singleton

    try:
        from app.knowledge_ingestions.workflow_repository import WorkflowRepository
        from app.retrieval.vector_retriever import VectorRetriever
        from app.retrieval.keyword_retriever import KeywordRetriever
        from app.retrieval.postgress_retriever import PostgressRetriever
        from app.retrieval.reciprocal_rank_fusion import ReciprocalRankFusion
        from app.retrieval.cross_encoder import CrossEncoderReRanker
        from app.retrieval.decision_engine import MappingDecisionEngine
        from app.retrieval.confidene_estimator import ConfidenceEstimator
        from app.retrieval.thresholds import RetrievalThresholds
        from app.retrieval.unknown_detector import UnkownDetetor
        from app.retrieval.pipeline import RetrievalPipeline
        from app.db.session import SessionLocal

        db = SessionLocal()
        try:
            repo = WorkflowRepository(db)
            _pipeline_singleton = RetrievalPipeline(
                vector_retriever   = VectorRetriever(repo),
                keyword_retriever  = KeywordRetriever(repo),
                postgres_retriever = PostgressRetriever(repo),
                rrf                = ReciprocalRankFusion(k=60),
                cross_encoder      = CrossEncoderReRanker(),
                decision_engine    = MappingDecisionEngine(
                    confidene_estimator = ConfidenceEstimator(),
                    thresholds          = RetrievalThresholds(),
                    unknown_detector    = UnkownDetetor(),
                ),
            )
        finally:
            db.close()

        # Embedder — optional; falls back to keyword-only if unavailable
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("BAAI/bge-small-en-v1.5")
            _embedder_singleton = lambda text: _model.encode(  # noqa: E731
                text, normalize_embeddings=True
            ).tolist()
        except Exception as exc:
            logger.warning(
                "runtime_dependencies_embedder_unavailable",
                extra={"extra_data": {"error": str(exc)}},
            )
            _embedder_singleton = None

        logger.info("runtime_dependencies_pipeline_ready")

    except Exception as exc:
        logger.error(
            "runtime_dependencies_pipeline_build_failed",
            extra={"extra_data": {"error": str(exc)}},
        )
        _pipeline_singleton = None
        _embedder_singleton = None


def get_retrieval_service(db: Session) -> ScopedRetrievalService | None:
    global _pipeline_singleton, _embedder_singleton

    if _pipeline_singleton is None:
        with _pipeline_lock:
            if _pipeline_singleton is None:
                _build_pipeline()

    if _pipeline_singleton is None:
        return None

    return ScopedRetrievalService(
        pipeline=_pipeline_singleton,
        db=db,
        embedder=_embedder_singleton,
    )


def get_orchestrator(db: Session) -> WorkflowRuntimeOrchestrator:
    """FastAPI dependency — returns a configured orchestrator per request."""
    return WorkflowRuntimeOrchestrator(
        db=db,
        retrieval_service=get_retrieval_service(db),
    )
