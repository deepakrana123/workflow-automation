"""
app/execution/runtime/retry_executor.py

Re-executes steps scheduled for retry via Redis.

Uses the identical dispatch path as StepExecutor:
    resolve_action_definition(action_name, workspace_id)
        ↓
    ExecutorRegistry.get_executor(execution_type)
        ↓
    executor.execute(action_definition, context)
        ↓
    ActionResult

This guarantees retry behaviour is always consistent with first-attempt behaviour.
"""

from app.models.workflow import Workflow
from app.execution.runtime.config_resolver import resolve_action_definition
from app.execution.executors.registry import get_executor as registry_get_executor
from app.execution.exceptions import ExecutorNotFoundError, HandlerNotFoundError
from app.workflow_execution.schemas.action_result import ActionResult

from app.execution.runtime.step_execution_service import (
    mark_step_running,
    mark_step_completed,
    mark_step_failed,
)
from app.execution.runtime.workflow_execution_service import mark_workflow_failed
from app.execution.runtime.workflow_finalizer import finalize_workflow_execution
from app.execution.retry_handler import handle_retry
from app.core.logger import logger


def execute_retry(db, workflow_execution, step_execution) -> None:
    """
    Re-run a RETRY_SCHEDULED step through the full executor pipeline.
    All outcomes (success, failure, further retry) are handled internally.
    """
    try:
        logger.info(
            "retry_execution_started",
            extra={"extra_data": {
                "workflow_execution_id": workflow_execution.id,
                "step_execution_id":     step_execution.id,
                "step_name":             step_execution.step_name,
            }},
        )

        db.refresh(workflow_execution)
        db.refresh(step_execution)

        if step_execution.status != "RETRY_SCHEDULED":
            logger.info(
                "retry_skipped_step_not_scheduled",
                extra={"extra_data": {
                    "step_execution_id": step_execution.id,
                    "status":            step_execution.status,
                }},
            )
            return

        mark_step_running(db=db, step_execution=step_execution)

        workflow = (
            db.query(Workflow)
            .filter(Workflow.id == workflow_execution.workflow_id)
            .first()
        )
        if not workflow:
            _handle_terminal_failure(
                db=db,
                workflow_execution=workflow_execution,
                step_execution=step_execution,
                error="workflow_definition_not_found_on_retry",
            )
            return

        workspace_id = workflow.workspace_id
        action       = step_execution.step_name

        action_def = resolve_action_definition(
            db=db,
            action_name=action,
            workspace_id=workspace_id,
        )

        if action_def is None:
            raise HandlerNotFoundError(
                handler_name=action,
                action_configuration_id=None,
            )

        template       = action_def.execution_template or {}
        execution_type = template.get("execution_type", "python")

        executor       = registry_get_executor(execution_type)
        result: ActionResult = executor.execute(
            action_definition=action_def,
            context=step_execution.input_payload or {},
        )

        logger.info(
            "execution_log",
            extra={"extra_data": {
                "workflow_id":          workflow_execution.workflow_id,
                "workspace_id":         workspace_id,
                "action_definition_id": action_def.id,
                "execution_type":       execution_type,
                "executor":             type(executor).__name__,
                "success":              result.success,
                "error":                result.error if not result.success else None,
            }},
        )

        if result.success:
            mark_step_completed(
                db=db,
                step_execution=step_execution,
                output_payload=result.model_dump(),
            )
            finalize_workflow_execution(db=db, workflow_execution=workflow_execution)
            logger.info(
                "retry_execution_completed",
                extra={"extra_data": {
                    "workflow_execution_id": workflow_execution.id,
                    "step_execution_id":     step_execution.id,
                }},
            )
            return

        step_error = result.error or str(result.outputs)
        mark_step_failed(db=db, step_execution=step_execution, error=step_error)
        handle_retry(
            db=db,
            step_execution=step_execution,
            error=step_error,
            workflow_execution=workflow_execution,
            skip_retry=result.metadata.get("skip_retry", False),
        )

    except (ExecutorNotFoundError, HandlerNotFoundError) as exc:
        logger.error(
            "retry_execution_config_error",
            extra={"extra_data": {
                "workflow_execution_id": workflow_execution.id,
                "step_execution_id":     step_execution.id,
                "error_type":            type(exc).__name__,
                "error":                 str(exc),
            }},
        )
        mark_step_failed(db=db, step_execution=step_execution, error=str(exc))
        handle_retry(
            db=db,
            step_execution=step_execution,
            error=str(exc),
            workflow_execution=workflow_execution,
            skip_retry=True,
        )

    except Exception as exc:
        logger.exception(
            "retry_execution_failed",
            extra={"extra_data": {
                "workflow_execution_id": workflow_execution.id,
                "step_execution_id":     step_execution.id,
                "error":                 str(exc),
            }},
        )
        try:
            if step_execution.status not in ("FAILED", "DLQ", "COMPLETED"):
                mark_step_failed(db=db, step_execution=step_execution, error=str(exc))
                handle_retry(
                    db=db,
                    step_execution=step_execution,
                    error=str(exc),
                    workflow_execution=workflow_execution,
                )
            if workflow_execution.status not in ("FAILED", "COMPLETED"):
                mark_workflow_failed(
                    db=db,
                    workflow_execution=workflow_execution,
                    error=str(exc),
                )
        except Exception as cleanup_exc:
            logger.error(
                "retry_execution_state_update_failed",
                extra={"extra_data": {
                    "workflow_execution_id": workflow_execution.id,
                    "step_execution_id":     step_execution.id,
                    "error":                 str(cleanup_exc),
                }},
            )


def _handle_terminal_failure(db, workflow_execution, step_execution, error: str) -> None:
    mark_step_failed(db=db, step_execution=step_execution, error=error)
    mark_workflow_failed(db=db, workflow_execution=workflow_execution, error=error)
