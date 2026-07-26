import time
import traceback

from app.execution.runtime.step_execution_service import (
    create_step_execution,
    mark_step_completed,
    mark_step_failed,
    mark_step_running,
)
from app.execution.executors.registry import ExecutorRegistry
from app.execution.retry_handler import handle_retry
from app.models.action_definitions import ActionDefinition
from app.repositories.action_configuration_repository import ActionConfigurationRepository
from app.repositories.step_retry_history_repo import record_retry_history
from app.workflow_execution.schemas.action_result import ActionResult
from app.core.logger import logger
from app.core.tracing import build_log_context, generate_span_id, inject_trace_into_payload
from app.services import trace_service


# ── Checkpoint labels ─────────────────────────────────────────────────────────
_CP_INIT           = "init"
_CP_CREATE_STEP    = "create_step_execution"
_CP_MARK_RUNNING   = "mark_step_running"
_CP_TRACE_STARTED  = "record_step_started"
_CP_INJECT_TRACE   = "inject_trace_into_payload"
_CP_LOAD_CONFIG    = "load_action_configuration"
_CP_DISPATCH       = "execute_action"
_CP_MARK_COMPLETED = "mark_step_completed"
_CP_MARK_FAILED    = "mark_step_failed"
_CP_RETRY          = "handle_retry"


def _load_action_configuration(
    db,
    action_name: str,
    workflow_knowledge_id: int | None,
):
    """
    Load ActionConfiguration using (workflow_knowledge_id, action_definition_id)
    when workflow_knowledge_id is available, otherwise fall back to action_definition_id
    alone.

    Returns (ActionConfiguration | None, execution_type: str)
    """
    try:
        action_def = (
            db.query(ActionDefinition)
            .filter(
                ActionDefinition.name == action_name,
                ActionDefinition.active.is_(True),
            )
            .first()
        )

        if action_def is None:
            return None, "python"

        repo = ActionConfigurationRepository(db)

        if workflow_knowledge_id is not None:
            # Primary path: exact lookup by (workflow_knowledge_id, action_definition_id)
            action_config = repo.get_active_configuration(
                workflow_knowledge_id=workflow_knowledge_id,
                action_definition_id=action_def.id,
            )
        else:
            # Fallback: lookup by action_definition_id only
            action_config = repo.get_by_action_definition(
                action_definition_id=action_def.id,
            )

        if action_config is None:
            return None, "python"

        return action_config, action_config.execution_type or "python"

    except Exception as e:
        logger.warning(
            "step_executor_config_lookup_failed",
            extra={"extra_data": {
                "action_name": action_name,
                "workflow_knowledge_id": workflow_knowledge_id,
                "error": str(e),
            }},
        )
        return None, "python"


def execute_workflow_step(
    db,
    workflow_execution,
    step_definition: dict,
    payload: dict,
    workflow_knowledge_id: int | None = None,
):
    step_execution = None
    checkpoint     = _CP_INIT

    try:
        action  = step_definition.get("action")
        step_id = step_definition.get("id", "unknown")

        span_id        = generate_span_id()
        parent_span_id = getattr(workflow_execution, "trace_id", None)

        logger.info(
            "step_execution_entering",
            extra={
                "extra_data": build_log_context(
                    workflow_execution=workflow_execution,
                    extra={
                        "step_id":        step_id,
                        "action":         action,
                        "span_id":        span_id,
                        "parent_span_id": str(parent_span_id) if parent_span_id else None,
                        "payload_keys":   list(payload.keys()) if payload else [],
                    },
                )
            },
        )

        # ── CHECKPOINT: create_step_execution ────────────────────────────────
        checkpoint = _CP_CREATE_STEP
        step_execution = create_step_execution(
            db=db,
            workflow_execution_id=workflow_execution.id,
            step_name=action or step_id,
            step_id=step_id,
            span_id=span_id,
            parent_span_id=str(parent_span_id) if parent_span_id else None,
            input_payload=payload,
        )

        # ── CHECKPOINT: mark_step_running ─────────────────────────────────────
        checkpoint = _CP_MARK_RUNNING
        mark_step_running(db=db, step_execution=step_execution)

        # ── CHECKPOINT: record_step_started ──────────────────────────────────
        checkpoint = _CP_TRACE_STARTED
        trace_service.record_step_started(
            db=db,
            workflow_execution=workflow_execution,
            step_execution=step_execution,
        )

        logger.info(
            "step_started",
            extra={
                "extra_data": build_log_context(
                    workflow_execution=workflow_execution,
                    execution_step=step_execution,
                    extra={"action": action},
                )
            },
        )

        # ── CHECKPOINT: inject_trace_into_payload ─────────────────────────────
        checkpoint = _CP_INJECT_TRACE
        traced_payload = inject_trace_into_payload(
            payload=payload,
            workflow_execution=workflow_execution,
            execution_step=step_execution,
        )

        trace_service.record_action_dispatched(
            db=db,
            workflow_execution=workflow_execution,
            step_execution=step_execution,
            action_name=action,
        )

        # ── CHECKPOINT: load_action_configuration ────────────────────────────
        checkpoint = _CP_LOAD_CONFIG
        action_config, execution_type = _load_action_configuration(
            db=db,
            action_name=action,
            workflow_knowledge_id=workflow_knowledge_id,
        )

        logger.info(
            "step_execution_dispatch_mode",
            extra={"extra_data": {
                "action":                action,
                "execution_type":        execution_type,
                "has_action_config":     action_config is not None,
                "workflow_knowledge_id": workflow_knowledge_id,
            }},
        )

        # ── CHECKPOINT: execute_action ────────────────────────────────────────
        checkpoint = _CP_DISPATCH

        if action_config is not None:
            executor      = ExecutorRegistry.get_executor(execution_type)
            executor_name = type(executor).__name__

            _t0 = time.perf_counter()
            result = executor.execute(
                configuration=action_config,
                context=traced_payload,
            )
            duration_ms = round((time.perf_counter() - _t0) * 1000, 2)

            logger.info(
                "execution_log",
                extra={"extra_data": {
                    "workflow_id":            getattr(workflow_execution, "workflow_id", None),
                    "workflow_knowledge_id":  workflow_knowledge_id,
                    "action_definition_id":   action_config.action_definition_id,
                    "execution_type":         execution_type,
                    "executor":               executor_name,
                    "duration_ms":            duration_ms,
                    "success":                result.success,
                    "error":                  result.error if not result.success else None,
                }},
            )
        else:
            # No ActionConfiguration found — step cannot be executed.
            # Return a non-retryable failure so the DAG can halt cleanly.
            logger.error(
                "step_executor_no_action_configuration",
                extra={"extra_data": {
                    "action":                action,
                    "workflow_knowledge_id": workflow_knowledge_id,
                }},
            )
            result = ActionResult(
                success=False,
                error=(
                    f"No ActionConfiguration found for action '{action}' "
                    f"(workflow_knowledge_id={workflow_knowledge_id})"
                ),
                metadata={"skip_retry": True},
            )

        success    = result.success
        skip_retry = result.metadata.get("skip_retry", False)

        if success:
            # ── CHECKPOINT: mark_step_completed ──────────────────────────────
            checkpoint = _CP_MARK_COMPLETED
            mark_step_completed(
                db=db,
                step_execution=step_execution,
                output_payload=result.model_dump(),
            )

            trace_service.record_action_success(
                db=db,
                workflow_execution=workflow_execution,
                step_execution=step_execution,
                action_name=action,
                result=result.model_dump(),
            )
            trace_service.record_step_completed(
                db=db,
                workflow_execution=workflow_execution,
                step_execution=step_execution,
                result=result.model_dump(),
            )

            logger.info(
                "step_completed",
                extra={
                    "extra_data": build_log_context(
                        workflow_execution=workflow_execution,
                        execution_step=step_execution,
                        extra={"action": action},
                    )
                },
            )

            return {"success": True, "result": result.model_dump()}

        # ── CHECKPOINT: mark_step_failed (non-success result) ─────────────────
        checkpoint = _CP_MARK_FAILED
        step_error = result.error or str(result.outputs)
        mark_step_failed(db=db, step_execution=step_execution, error=step_error)

        trace_service.record_action_failed(
            db=db,
            workflow_execution=workflow_execution,
            step_execution=step_execution,
            action_name=action,
            error=step_error,
        )
        trace_service.record_step_failed(
            db=db,
            workflow_execution=workflow_execution,
            step_execution=step_execution,
            error=step_error,
        )

        logger.warning(
            "step_failed",
            extra={
                "extra_data": build_log_context(
                    workflow_execution=workflow_execution,
                    execution_step=step_execution,
                    extra={"action": action, "error": step_error},
                )
            },
        )

        # ── CHECKPOINT: handle_retry ──────────────────────────────────────────
        checkpoint = _CP_RETRY
        retry_result = handle_retry(
            db=db,
            step_execution=step_execution,
            error=step_error,
            workflow_execution=workflow_execution,
            skip_retry=skip_retry,
        )

        record_retry_history(
            db=db,
            step_execution=step_execution,
            attempt_number=retry_result.get("attempts", 1),
            trigger="retry" if retry_result.get("retry_scheduled") else "dlq",
            status_at_attempt=step_execution.status,
            error=step_error,
        )

        return {"success": False, "result": result.model_dump()}

    except Exception as e:
        logger.error(
            "step_execution_failed",
            extra={
                "extra_data": {
                    **build_log_context(
                        workflow_execution=workflow_execution,
                        execution_step=step_execution,
                    ),
                    "failed_at_checkpoint":  checkpoint,
                    "error":                 str(e),
                    "error_type":            type(e).__name__,
                    "traceback":             traceback.format_exc(),
                    "step_id":               step_definition.get("id", "unknown"),
                    "action":                step_definition.get("action"),
                    "payload_keys":          list(payload.keys()) if payload else [],
                    "payload_has_trace":     "_trace" in (payload or {}),
                    "step_execution_id":     getattr(step_execution, "id", None),
                    "step_status":           getattr(step_execution, "status", None),
                    "span_id":               getattr(step_execution, "span_id", None),
                }
            },
        )

        if step_execution:
            if step_execution.status not in ("FAILED", "RETRY_SCHEDULED", "DLQ", "COMPLETED"):
                try:
                    mark_step_failed(
                        db=db, step_execution=step_execution, error=str(e)
                    )
                    trace_service.record_step_failed(
                        db=db,
                        workflow_execution=workflow_execution,
                        step_execution=step_execution,
                        error=str(e),
                    )
                    retry_result = handle_retry(
                        db=db,
                        step_execution=step_execution,
                        error=str(e),
                        workflow_execution=workflow_execution,
                    )
                    record_retry_history(
                        db=db,
                        step_execution=step_execution,
                        attempt_number=retry_result.get("attempts", 1),
                        trigger="retry" if retry_result.get("retry_scheduled") else "dlq",
                        status_at_attempt=step_execution.status,
                        error=str(e),
                    )
                except Exception as cleanup_err:
                    logger.error(
                        "step_execution_cleanup_failed",
                        extra={
                            "extra_data": {
                                "step_execution_id":   getattr(step_execution, "id", None),
                                "original_checkpoint": checkpoint,
                                "cleanup_error":       str(cleanup_err),
                                "cleanup_error_type":  type(cleanup_err).__name__,
                                "cleanup_traceback":   traceback.format_exc(),
                            }
                        },
                    )

        return {"success": False, "error": str(e)}
