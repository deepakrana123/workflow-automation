from dataclasses import dataclass

from enum import Enum


class RetrievalType(Enum):
    ACTION = "action"
    TRIGGER = "trigger"


# Confidence thresholds for accepting a retrieval match (confidence is the
# sigmoid of the cross-encoder score). Lowered from 0.65/0.60 after empirical
# calibration: once the cross-encoder document includes the catalog description
# (see cross_encoder._candidate_text), correct-but-reworded matches score well
# above 0.40 while genuine non-matches stay at/below ~0.14 — so 0.40 recovers
# real matches (e.g. "Validate PAN Details" -> verify_pan) with zero observed
# false positives and a wide safety margin.
@dataclass(frozen=True)
class RetrievalThresholds:
    action_threshold: float = 0.40
    trigger_threshold: float = 0.40
    unknown_margin: float = 0.08
