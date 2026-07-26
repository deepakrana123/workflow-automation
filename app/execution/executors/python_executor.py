"""
app/execution/executors/python_executor.py

Executes internal Python handlers registered in the dispatcher ACTION_MAP.

Flow:
    ActionConfiguration.configuration["handler"]
        ↓
    ACTION_MAP lookup
        ↓
    handler(payload, config)  →  ActionResult
"""

from app.execution.executors.base_executor import BaseExecutor
from app.models.action_configurations_model import ActionConfiguration
from app.workflow_execution.schemas.action_result import ActionResult
from app.core.logger import logger


class PythonExecutor(BaseExecutor):

    def execute(
        self,
        configuration: ActionConfiguration,
        context: dict,
    ) -> ActionResult:
        # Import here to avoid circular import at module load time
        from app.execution.action_registry import ACTION_MAP

        cfg = configuration.configuration or {}
        handler_name = cfg.get("handler")

        if not handler_name:
            logger.error(
                "python_executor_missing_handler",
                extra={"extra_data": {
                    "action_configuration_id": configuration.id,
                    "configuration": cfg,
                }},
            )
            return ActionResult(
                success=False,
                error="python_executor: no handler defined in configuration",
                metadata={"skip_retry": True},
            )

        handler = ACTION_MAP.get(handler_name)

        if not handler:
            logger.error(
                "python_executor_handler_not_found",
                extra={"extra_data": {
                    "handler_name": handler_name,
                    "action_configuration_id": configuration.id,
                }},
            )
            return ActionResult(
                success=False,
                error=f"python_executor: handler '{handler_name}' not in ACTION_MAP",
                metadata={"skip_retry": True},
            )

        logger.info(
            "python_executor_dispatching",
            extra={"extra_data": {"handler_name": handler_name}},
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
