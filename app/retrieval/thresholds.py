from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalThresholds:
    action_threshold: float = 0.65
    trigger_threshold: float = 0.60
    unknown_margin: float = 0.08