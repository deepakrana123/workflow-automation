"""
app/execution/executors/human_executor.py

HumanExecutor — suspends the workflow at this step for a human decision.

Returns an ActionResult carrying a WAITING marker in ``metadata``.
The step executor detects that marker, records the step as WAITING,
and persists a HumanTask row; the DAG halts until an operator decides.
"""

from app.execution.executors.base_executor import BaseExecutor
from app.execution.executors.constants import EXECUTION_STATUS_WAITING
from app.models.action_definitions import ActionDefinition
from app.workflow_execution.schemas.action_result import ActionResult
from app.core.logger import logger

_VALID_TIMEOUT_DECISIONS = {"approve", "reject"}
_DEFAULT_ON_TIMEOUT = "reject"


class HumanExecutor(BaseExecutor):
    """Suspend a step pending a human Approve/Reject decision."""

    def execute(
        self,
        action_definition: ActionDefinition,
        context: dict,
    ) -> ActionResult:
        template = action_definition.execution_template or {}
        cfg = template.get("configuration") or {}

        prompt = cfg.get("prompt", "Manual approval required.")
        timeout_seconds = cfg.get("timeout_seconds")

        on_timeout = str(cfg.get("on_timeout", _DEFAULT_ON_TIMEOUT)).lower()
        if on_timeout not in _VALID_TIMEOUT_DECISIONS:
            on_timeout = _DEFAULT_ON_TIMEOUT

        logger.info(
            "human_task_suspending",
            extra={"extra_data": {
                "action_definition_id": action_definition.id,
                "action_name": action_definition.name,
                "on_timeout": on_timeout,
                "has_timeout": timeout_seconds is not None,
            }},
        )

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
