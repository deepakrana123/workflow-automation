from app.retrieval.models import RankedCandidate
from app.retrieval.thresholds import RetrievalThresholds
from app.retrieval.confidene_estimator import ConfidenceEstimator


class MappingDecisionEngine:
    def __init__(
        self, confidene_estimator: ConfidenceEstimator, thresholds: RetrievalThresholds
    ):
        self.confidence_estimator = confidene_estimator
        self.thresholds = thresholds

    def decide(
        self, candidates: list[RankedCandidate], entity_type: str
    ) -> RankedCandidate | None:
        if not candidates:
            return None

        best = candidates[0]
        confidence = self.confidence_estimator.estimate(best)
        thresholds = (
            self.thresholds.action_threshold
            if entity_type == "action"
            else self.thresholds.trigger_threshold
        )
        
        if confidence < thresholds:
            return None
        return best
            
