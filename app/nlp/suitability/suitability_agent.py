from dataclasses import dataclass
from typing import Optional

# When workflow_type cannot be determined from the catalog (e.g. all mapping
# rows have workflow_type=NULL), fall back to the primary domain rather than
# blocking generation entirely.
# Hardcoded to "finance" — the current sole domain. When ALLOWED_DOMAINS grows,
# this should be passed in from the request domain instead.
_DEFAULT_WORKFLOW_TYPE = "finance"


@dataclass
class SuitabilityResult:
    supported: bool
    reason: Optional[str] = None
    workflow_type: Optional[str] = None


class SuitabilityAgent:

    def evaluate(
        self,
        workflow_type: Optional[str],
        matched_triggers,
        matched_actions,
    ) -> SuitabilityResult:
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

        # workflow_type may be None when all mapping rows have null workflow_type
        # snapshots (legacy rows before the snapshot migration). Fall back to the
        # default domain so generation is not blocked on a missing metadata field.
        resolved_type = workflow_type or _DEFAULT_WORKFLOW_TYPE

        return SuitabilityResult(
            supported=True,
            workflow_type=resolved_type,
        )
