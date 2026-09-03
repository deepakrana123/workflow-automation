"""
app/retrieval/pipeline.py

RetrievalPipeline — orchestrates the full retrieval stack for a single query.

Responsibilities:
  - Run three retrievers in parallel (vector, BM25, Postgres FTS)
  - Fuse results with Reciprocal Rank Fusion
  - Re-rank with the cross-encoder
  - Apply the MappingDecisionEngine threshold to return a single winner or None

This class is the only component that knows about the internal retrieval stages.
EmbeddingMapper calls search_actions / search_triggers and receives either a
RankedCandidate (confident match) or None (below threshold / no candidates).

Nothing here touches the database — that remains WorkflowRepository's job.
"""

from app.retrieval.vector_retriever import VectorRetriever
from app.retrieval.keyword_retriever import KeywordRetriever
from app.retrieval.postgress_retriever import PostgressRetriever
from app.retrieval.reciprocal_rank_fusion import ReciprocalRankFusion
from app.retrieval.cross_encoder import CrossEncoderReRanker
from app.retrieval.decision_engine import MappingDecisionEngine
from app.retrieval.thresholds import RetrievalType
from app.retrieval.models import RankedCandidate


class RetrievalPipeline:
    """
    Full retrieval pipeline: retrieve → fuse → rerank → decide.

    Constructed via dependency injection — no component is created internally.

    Usage:
        pipeline = RetrievalPipeline(
            vector_retriever,
            keyword_retriever,
            postgres_retriever,
            rrf,
            cross_encoder,
            decision_engine,
        )

        best = pipeline.search_actions(query, embedding)
        # returns RankedCandidate or None
    """

    def __init__(
        self,
        vector_retriever: VectorRetriever,
        keyword_retriever: KeywordRetriever,
        postgres_retriever: PostgressRetriever,
        rrf: ReciprocalRankFusion,
        cross_encoder: CrossEncoderReRanker,
        decision_engine: MappingDecisionEngine,
    ):
        self._vector = vector_retriever
        self._keyword = keyword_retriever
        self._postgres = postgres_retriever
        self._rrf = rrf
        self._cross = cross_encoder
        self._decision = decision_engine

    # ── Public interface ──────────────────────────────────────────────────────

    def search_actions(
        self,
        query: str,
        embedding: list[float],
        limit: int = 50,
    ) -> RankedCandidate | None:
        """
        Run the full pipeline for an action query.

        Returns the best RankedCandidate above the action confidence threshold,
        or None if no candidate meets the threshold.
        """
        candidates = self._retrieve_and_rank_actions(query, embedding, limit)
        return self._decision.decide(candidates, entity_type=RetrievalType.ACTION)

    def search_triggers(
        self,
        query: str,
        embedding: list[float],
        limit: int = 50,
    ) -> RankedCandidate | None:
        """
        Run the full pipeline for a trigger query.

        Returns the best RankedCandidate above the trigger confidence threshold,
        or None if no candidate meets the threshold.
        """
        candidates = self._retrieve_and_rank_triggers(query, embedding, limit)
        return self._decision.decide(candidates, entity_type=RetrievalType.TRIGGER)

    def retrieve_actions(
        self,
        query: str,
        embedding: list[float],
        limit: int = 50,
    ) -> list[RankedCandidate]:
        """
        Return the full ranked candidate list for actions (no decision filter).

        Used by evaluation to get top-N candidates for ranking breakdown.
        """
        return self._retrieve_and_rank_actions(query, embedding, limit)

    def retrieve_triggers(
        self,
        query: str,
        embedding: list[float],
        limit: int = 50,
    ) -> list[RankedCandidate]:
        """
        Return the full ranked candidate list for triggers (no decision filter).

        Used by evaluation to get top-N candidates for ranking breakdown.
        """
        return self._retrieve_and_rank_triggers(query, embedding, limit)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _retrieve_and_rank_actions(
        self, query: str, embedding: list[float], limit: int
    ) -> list[RankedCandidate]:
        vector_results   = self._vector.search_actions(embedding, limit=limit)
        keyword_results  = self._keyword.search_actions(query, limit=limit)
        postgres_results = self._postgres.search_actions(query, limit=limit)
        fused = self._rrf.fuse(vector_results, keyword_results, postgres_results)
        return self._cross.rerank(query, fused)

    def _retrieve_and_rank_triggers(
        self, query: str, embedding: list[float], limit: int
    ) -> list[RankedCandidate]:
        vector_results   = self._vector.search_triggers(embedding, limit=limit)
        keyword_results  = self._keyword.search_triggers(query, limit=limit)
        postgres_results = self._postgres.search_triggers(query, limit=limit)
        fused = self._rrf.fuse(vector_results, keyword_results, postgres_results)
        return self._cross.rerank(query, fused)
