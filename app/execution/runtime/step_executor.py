"""
app/execution/runtime/step_executor.py

Executes a single workflow step.

Flow:
    ActionConfiguration  (resolved via config_resolver)
        ↓
    ExecutorRegistry.get_executor(execution_type)
        ↓
    executor.execute(configuration, context)
        ↓
    ActionResult  →  mark completed / failed / retry / DLQ
"""

import time
import traceback

from app.execution.runtime.step_execution_service import (
    create_step_execution,
    mark_step_completed,
    mark_step_failed,
    mark_step_running,
)
from app.execution.runtime.config_resolver import resolve_action_configuration
from app.execution.executors.registry import get_executor as registry_get_executor
from app.execution.exceptions import (
    ConfigurationNotFoundError,
    ExecutorNotFoundError,
    HandlerNotFoundError,
)
from app.execution.retry_handler import handle_retry
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
_CP_DISPATCH       = "executor_dispatch"
_CP_MARK_COMPLETED = "mark_step_completed"
_CP_MARK_FAILED    = "mark_step_failed"
_CP_RETRY          = "handle_retry"


def execute_workflow_step(
    db,
    workflow_execution,
    step_definition: dict,
    payload: dict,
    workflow_knowledge_id: int | None = None,
) -> dict:
    """
    Execute one step of the workflow DAG.

    Returns {"success": True/False, "result": ...}
    Never raises — all exceptions are caught and converted to failure results.
    """
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
        action_config, execution_type = resolve_action_configuration(
            db=db,
            action_name=action,
            workflow_knowledge_id=workflow_knowledge_id,
        )

        if action_config is None:
            raise ConfigurationNotFoundError(
                action_name=action,
                workflow_knowledge_id=workflow_knowledge_id,
            )

        # ── CHECKPOINT: executor_dispatch ────────────────────────────────────
        checkpoint = _CP_DISPATCH

        executor      = registry_get_executor(execution_type)
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
                "workflow_id":           getattr(workflow_execution, "workflow_id", None),
                "workflow_knowledge_id": workflow_knowledge_id,
                "action_definition_id":  action_config.action_definition_id,
                "execution_type":        execution_type,
                "executor":              executor_name,
                "duration_ms":           duration_ms,
                "success":               result.success,
                "error":                 result.error if not result.success else None,
            }},
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

        # ── CHECKPOINT: mark_step_failed ──────────────────────────────────────
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

    except (ConfigurationNotFoundError, ExecutorNotFoundError, HandlerNotFoundError) as exc:
        # Non-retryable execution errors — known, specific, no stack trace needed
        step_error = str(exc)
        logger.error(
            "step_execution_error",
            extra={
                "extra_data": {
                    **build_log_context(
                        workflow_execution=workflow_execution,
                        execution_step=step_execution,
                    ),
                    "failed_at_checkpoint": checkpoint,
                    "error_type":           type(exc).__name__,
                    "error":                step_error,
                    "step_id":              step_definition.get("id", "unknown"),
                    "action":               step_definition.get("action"),
                }
            },
        )
        if step_execution and step_execution.status not in (
            "FAILED", "RETRY_SCHEDULED", "DLQ", "COMPLETED"
        ):
            try:
                mark_step_failed(db=db, step_execution=step_execution, error=step_error)
                handle_retry(
                    db=db,
                    step_execution=step_execution,
                    error=step_error,
                    workflow_execution=workflow_execution,
                    skip_retry=True,  # non-retryable
                )
            except Exception:
                pass
        return {"success": False, "error": step_error}

    except Exception as exc:
        # Unexpected exceptions — full traceback for diagnosis
        step_error = str(exc)
        logger.error(
            "step_execution_failed",
            extra={
                "extra_data": {
                    **build_log_context(
                        workflow_execution=workflow_execution,
                        execution_step=step_execution,
                    ),
                    "failed_at_checkpoint": checkpoint,
                    "error":                step_error,
                    "error_type":           type(exc).__name__,
                    "traceback":            traceback.format_exc(),
                    "step_id":              step_definition.get("id", "unknown"),
                    "action":               step_definition.get("action"),
                    "payload_keys":         list(payload.keys()) if payload else [],
                    "payload_has_trace":    "_trace" in (payload or {}),
                    "step_execution_id":    getattr(step_execution, "id", None),
                    "step_status":          getattr(step_execution, "status", None),
                    "span_id":              getattr(step_execution, "span_id", None),
                }
            },
        )
        if step_execution and step_execution.status not in (
            "FAILED", "RETRY_SCHEDULED", "DLQ", "COMPLETED"
        ):
            try:
                mark_step_failed(db=db, step_execution=step_execution, error=step_error)
                trace_service.record_step_failed(
                    db=db,
                    workflow_execution=workflow_execution,
                    step_execution=step_execution,
                    error=step_error,
                )
                retry_result = handle_retry(
                    db=db,
                    step_execution=step_execution,
                    error=step_error,
                    workflow_execution=workflow_execution,
                )
                record_retry_history(
                    db=db,
                    step_execution=step_execution,
                    attempt_number=retry_result.get("attempts", 1),
                    trigger="retry" if retry_result.get("retry_scheduled") else "dlq",
                    status_at_attempt=step_execution.status,
                    error=step_error,
                )
            except Exception as cleanup_exc:
                logger.error(
                    "step_execution_cleanup_failed",
                    extra={"extra_data": {
                        "step_execution_id":   getattr(step_execution, "id", None),
                        "original_checkpoint": checkpoint,
                        "cleanup_error":       str(cleanup_exc),
                        "cleanup_traceback":   traceback.format_exc(),
                    }},
                )
        return {"success": False, "error": step_error}
