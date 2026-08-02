"""
app/execution/executors/python_executor.py

Executes internal Python handlers via ActionHandlerRegistry.

Flow:
    ActionConfiguration.configuration["handler"]
        ↓
    ActionHandlerRegistry lookup
        ↓
    handler(context, configuration)  →  ActionResult
"""

from app.execution.executors.base_executor import BaseExecutor
from app.execution.exceptions import HandlerNotFoundError
from app.models.action_configurations_model import ActionConfiguration
from app.workflow_execution.schemas.action_result import ActionResult
from app.core.logger import logger


class PythonExecutor(BaseExecutor):

    def execute(
        self,
        configuration: ActionConfiguration,
        context: dict,
    ) -> ActionResult:
        # Deferred import — breaks potential circular import at module load time
        from app.execution.python.action_handler_registry import ACTION_HANDLER_MAP

        cfg          = configuration.configuration or {}
        handler_name = cfg.get("handler")

        if not handler_name:
            raise HandlerNotFoundError(
                handler_name=None,
                action_configuration_id=configuration.id,
            )

        handler = ACTION_HANDLER_MAP.get(handler_name)

        if not handler:
            raise HandlerNotFoundError(
                handler_name=handler_name,
                action_configuration_id=configuration.id,
            )

        logger.info(
            "python_executor_dispatching",
            extra={"extra_data": {
                "handler_name":            handler_name,
                "action_configuration_id": configuration.id,
            }},
        )

        raw = handler(context, cfg)

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
