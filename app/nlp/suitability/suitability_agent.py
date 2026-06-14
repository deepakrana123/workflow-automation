from dataclasses import dataclass
from typing import Optional


@dataclass
class SuitabilityResult:
    supported: bool
    reason: Optional[str] = None


class SuitabilityAgent:
    def evaluate(
        Self, workflow_type: Optional[str], matched_triggers, matched_actions
    ) -> SuitabilityResult:
        if not workflow_type:
            return SuitabilityResult(
                supported=False,
                reason="workflow_type_not_detected",
            )
        if not matched_triggers:
            return SuitabilityResult(
                supported=False,
                reason="trigger_not_found",
            )

        if not matched_actions:
            return SuitabilityResult(
                supported=False,
                reason="action_not_found",
            )

        return SuitabilityResult(
            supported=True,
        )
