from dataclasses import dataclass

from enum import Enum


class RetrievalType(Enum):
    ACTION = "action"
    TRIGGER = "trigger"


@dataclass(frozen=True)
class RetrievalThresholds:
    action_threshold: float = 0.65
    trigger_threshold: float = 0.60
    unknown_margin: float = 0.08
