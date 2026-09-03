"""
app/execution/executors/python_executor.py

Executes internal Python handlers via ActionHandlerRegistry.

Flow:
    ActionDefinition.name
        ↓
    ActionHandlerRegistry lookup  (handler key = action name)
        ↓
    handler(context, action_definition)  →  ActionResult
"""

from app.execution.executors.base_executor import BaseExecutor
from app.execution.exceptions import HandlerNotFoundError
from app.models.action_definitions import ActionDefinition
from app.workflow_execution.schemas.action_result import ActionResult
from app.core.logger import logger


class PythonExecutor(BaseExecutor):

    def execute(
        self,
        action_definition: ActionDefinition,
        context: dict,
    ) -> ActionResult:
        # Deferred import — breaks potential circular import at module load time
        from app.execution.python.action_handler_registry import ACTION_HANDLER_MAP

        handler_name = action_definition.name

        handler = ACTION_HANDLER_MAP.get(handler_name)

        if not handler:
            raise HandlerNotFoundError(
                handler_name=handler_name,
                action_configuration_id=None,
            )

        logger.info(
            "python_executor_dispatching",
            extra={"extra_data": {
                "handler_name":       handler_name,
                "action_definition_id": action_definition.id,
            }},
        )

        raw = handler(context, {})

        # Normalise — handler may return ActionResult or legacy dict
        if isinstance(raw, ActionResult):
            return raw

        success = raw.get("success", False) or raw.get("status") == "success"
        outputs = {
            k: v for k, v in raw.items()
            if k not in ("success", "status", "skip_retry", "message", "error")
        }
        return ActionResult(
            success=success,
            outputs=outputs,
            message=raw.get("message"),
            error=raw.get("error"),
            metadata={"skip_retry": raw.get("skip_retry", False)},
        )
