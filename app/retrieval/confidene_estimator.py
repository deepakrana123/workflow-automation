"""
app/retrieval/confidene_estimator.py

Confidence estimator for a single RankedCandidate.

After cross-encoder re-ranking, cross_encoder_score is the primary signal.
It is a raw logit, so we pass it through a sigmoid to get a 0–1 probability.

If cross_encoder_score is not available (re-ranker was skipped), we fall back
to rrf_score which is already normalised to a small positive float.
"""

import math
from app.retrieval.models import RankedCandidate


def _sigmoid(x: float) -> float:
    """Map a real-valued logit to (0, 1)."""
    return 1.0 / (1.0 + math.exp(-x))


class ConfidenceEstimator:
    def estimate(self, candidate: RankedCandidate) -> float:
        """
        Return a confidence score in [0, 1].

        Priority:
          1. cross_encoder_score  — sigmoid-normalised logit (more reliable)
          2. rrf_score            — used as-is when cross-encoder was not run
        """
        if candidate.cross_encoder_score is not None:
            return _sigmoid(candidate.cross_encoder_score)
        return float(candidate.rrf_score)
