"""
app/retrieval/decision_engine.py

Decides whether the top-ranked candidate is a confident match or UNKNOWN.

Uses:
  - ConfidenceEstimator  — converts raw scores to a [0,1] confidence value
  - RetrievalThresholds  — per-type minimum confidence thresholds
  - UnknownDetector      — compares confidence against the threshold
"""

from app.retrieval.models import RankedCandidate
from app.retrieval.thresholds import RetrievalThresholds, RetrievalType
from app.retrieval.confidene_estimator import ConfidenceEstimator
from app.retrieval.unknown_detector import UnkownDetetor


class MappingDecisionEngine:
    def __init__(
        self,
        confidene_estimator: ConfidenceEstimator,
        thresholds: RetrievalThresholds,
        unknown_detector: UnkownDetetor,
    ):
        self.confidence_estimator = confidene_estimator
        self.thresholds = thresholds
        self.unknown_detector = unknown_detector

    def decide(
        self,
        candidates: list[RankedCandidate],
        entity_type: RetrievalType,          # ← enum, not a plain string
    ) -> RankedCandidate | None:
        """
        Return the best candidate if confidence exceeds the threshold,
        otherwise return None (treated as UNKNOWN by the mapper).
        """
        if not candidates:
            return None

        best = candidates[0]
        confidence = self.confidence_estimator.estimate(best)

        # Fix: compare enum to enum, not enum to string
        threshold = (
            self.thresholds.action_threshold
            if entity_type == RetrievalType.ACTION
            else self.thresholds.trigger_threshold
        )

        if self.unknown_detector.is_unknown(confidence, threshold):
            return None

        return best
