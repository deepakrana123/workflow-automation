"""
app/retrieval/cross_encoder.py

Cross-encoder re-ranker.

Takes the top-N candidates from RRF fusion and re-scores each one by running
the query and the candidate name+description through a cross-encoder model
(joint encoding — much more accurate than bi-encoder similarity).

Model: cross-encoder/ms-marco-MiniLM-L-6-v2
  - Small, fast, strong general-purpose re-ranker
  - Outputs a raw logit score (higher = more relevant)

The rerank() method:
  1. Builds (query, candidate_text) pairs
  2. Scores all pairs in one batched forward pass
  3. Attaches the score to cross_encoder_score on each RankedCandidate
  4. Returns the list sorted by cross_encoder_score descending
"""

from sentence_transformers import CrossEncoder as _CrossEncoder
from app.retrieval.models import RankedCandidate


_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderReRanker:
    def __init__(self, model_name: str = _MODEL_NAME, top_k: int = 20):
        """
        model_name  — HuggingFace cross-encoder model to load
        top_k       — only re-rank the top-k candidates from RRF
                      (rest are discarded; keeps latency low)
        """
        self.model = _CrossEncoder(model_name)
        self.top_k = top_k

    def rerank(
        self,
        query: str,
        candidates: list[RankedCandidate],
    ) -> list[RankedCandidate]:
        """
        Re-rank candidates using cross-encoder scores.

        Returns a new list sorted by cross_encoder_score descending.
        Candidates beyond top_k are dropped before scoring.
        """
        if not candidates:
            return []

        pool = candidates[: self.top_k]

        # Build (query, document_text) pairs
        pairs = [
            (query, self._candidate_text(c))
            for c in pool
        ]

        scores: list[float] = self.model.predict(pairs).tolist()

        for candidate, score in zip(pool, scores):
            candidate.cross_encoder_score = float(score)

        pool.sort(key=lambda c: c.cross_encoder_score, reverse=True)
        return pool

    @staticmethod
    def _candidate_text(candidate: RankedCandidate) -> str:
        """Build the document string shown to the cross-encoder."""
        name = getattr(candidate.entity, "name", "") or ""
        desc = getattr(candidate.entity, "description", "") or ""
        return f"{name} {desc}".strip()
