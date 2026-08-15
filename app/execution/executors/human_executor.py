"""
app/execution/executors/human_executor.py

HumanExecutor — suspends the workflow at this step for a human decision.

Unlike Python/HTTP executors, a human task does not complete synchronously.
It returns an ActionResult carrying a WAITING marker (and the human-task
spec) in ``metadata``. The step executor detects that marker, records the
step as WAITING, and persists a HumanTask row; the DAG halts until an operator
approves or rejects.

Kept intentionally simple (MVP): Approve / Reject / Timeout(->approve|reject).
No roles, escalation, delegation or SLA — those are future concerns, and
because this is a normal executor, its behaviour can later be driven by
business rules without touching the DAG engine.
"""

from app.execution.executors.base_executor import BaseExecutor
from app.execution.executors.constants import EXECUTION_STATUS_WAITING
from app.models.action_configurations_model import ActionConfiguration
from app.workflow_execution.schemas.action_result import ActionResult
from app.core.logger import logger

_VALID_TIMEOUT_DECISIONS = {"approve", "reject"}
_DEFAULT_ON_TIMEOUT = "reject"


class HumanExecutor(BaseExecutor):
    """Suspend a step pending a human Approve/Reject decision."""

    def execute(
        self,
        configuration: ActionConfiguration,
        context: dict,
    ) -> ActionResult:
        cfg = configuration.configuration or {}

        prompt = cfg.get("prompt", "Manual approval required.")
        timeout_seconds = cfg.get("timeout_seconds")

        on_timeout = str(cfg.get("on_timeout", _DEFAULT_ON_TIMEOUT)).lower()
        if on_timeout not in _VALID_TIMEOUT_DECISIONS:
            on_timeout = _DEFAULT_ON_TIMEOUT

        logger.info(
            "human_task_suspending",
            extra={"extra_data": {
                "action_configuration_id": configuration.id,
                "on_timeout": on_timeout,
                "has_timeout": timeout_seconds is not None,
            }},
        )

        # success=False is intentional but never interpreted as a failure:
        # the step executor checks the WAITING marker BEFORE the success flag.
        return ActionResult(
            success=False,
            message="Awaiting human approval.",
            metadata={
                "execution_status": EXECUTION_STATUS_WAITING,
                "human_task": {
                    "prompt": prompt,
                    "timeout_seconds": timeout_seconds,
                    "on_timeout": on_timeout,
                },
            },
        )
