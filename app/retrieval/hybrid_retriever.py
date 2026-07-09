"""
app/retrieval/hybrid_retriever.py

HybridRetriever — owns the embedding model and delegates retrieval to RetrievalPipeline.

Responsibilities:
  - embed()  : encode a text string into a dense vector
  - search_actions / search_triggers : thin pass-through to RetrievalPipeline
    (kept for backward compatibility with evaluation's ranking re-run)

The retrieval orchestration (vector + BM25 + Postgres + RRF + cross-encoder +
decision) lives entirely in RetrievalPipeline. HybridRetriever does not
duplicate any of that logic.
"""

from sentence_transformers import SentenceTransformer

from .pipeline import RetrievalPipeline
from .models import RankedCandidate


class HybridRetriever:
    """
    Thin wrapper that bundles the embedding model with a RetrievalPipeline.

    EmbeddingMapper uses RetrievalPipeline directly.
    Evaluation (test_extractor) uses HybridRetriever.embed() + pipeline.retrieve_*()
    for the ranking breakdown re-run.
    """

    def __init__(
        self,
        pipeline: RetrievalPipeline,
        model_name: str = "BAAI/bge-small-en-v1.5",
    ):
        self.pipeline = pipeline
        self.model = SentenceTransformer(model_name)

    def embed(self, text: str) -> list[float]:
        vector = self.model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    # ── Pass-throughs used by evaluation ranking re-run ───────────────────────

    def search_actions(
        self, query: str, embedding: list[float], limit: int = 50
    ) -> list[RankedCandidate]:
        """Return full candidate list (no decision filter) — used by evaluation."""
        return self.pipeline.retrieve_actions(query, embedding, limit=limit)

    def search_triggers(
        self, query: str, embedding: list[float], limit: int = 50
    ) -> list[RankedCandidate]:
        """Return full candidate list (no decision filter) — used by evaluation."""
        return self.pipeline.retrieve_triggers(query, embedding, limit=limit)
