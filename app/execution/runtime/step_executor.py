import traceback
from app.execution.runtime.step_execution_service import (
    mark_step_running,
    mark_step_completed,
    mark_step_failed,
    create_step_execution,
)
from app.execution.dispatcher import execute_action
from app.execution.retry_handler import handle_retry
from app.repositories.step_retry_history_repo import record_retry_history
from app.core.tracing import generate_span_id, inject_trace_into_payload, build_log_context
from app.services import trace_service
from app.core.logger import logger


# Checkpoint labels — every major operation inside execute_workflow_step
# gets a checkpoint so the except block can tell you exactly where it crashed
_CP_INIT            = "init"
_CP_CREATE_STEP     = "create_step_execution"
_CP_MARK_RUNNING    = "mark_step_running"
_CP_TRACE_STARTED   = "record_step_started"
_CP_INJECT_TRACE    = "inject_trace_into_payload"
_CP_DISPATCH        = "execute_action"
_CP_MARK_COMPLETED  = "mark_step_completed"
_CP_MARK_FAILED     = "mark_step_failed"
_CP_RETRY           = "handle_retry"


def execute_workflow_step(db, workflow_execution, step_definition, payload):

    step_execution = None
    checkpoint     = _CP_INIT   # tracks last successfully passed checkpoint

    try:
        action  = step_definition.get("action")
        config  = step_definition.get("config", {})
        step_id = step_definition.get("id", "unknown")

        span_id        = generate_span_id()
        parent_span_id = getattr(workflow_execution, "trace_id", None)

        logger.info(
            "step_execution_entering",
            extra={
                "extra_data": build_log_context(
                    workflow_execution=workflow_execution,
                    extra={
                        "step_id": step_id,
                        "action": action,
                        "span_id": span_id,
                        "parent_span_id": str(parent_span_id) if parent_span_id else None,
                        "payload_keys": list(payload.keys()) if payload else [],
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

        # ── CHECKPOINT: execute_action ────────────────────────────────────────
        checkpoint = _CP_DISPATCH
        result  = execute_action(action_name=action, payload=traced_payload, config=config)
        success = result.get("success") is True or result.get("status") == "success"

        if success:
            # ── CHECKPOINT: mark_step_completed ──────────────────────────────
            checkpoint = _CP_MARK_COMPLETED
            mark_step_completed(
                db=db, step_execution=step_execution, output_payload=result
            )

            trace_service.record_action_success(
                db=db,
                workflow_execution=workflow_execution,
                step_execution=step_execution,
                action_name=action,
                result=result,
            )
            trace_service.record_step_completed(
                db=db,
                workflow_execution=workflow_execution,
                step_execution=step_execution,
                result=result,
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

            return {"success": True, "result": result}

        # ── CHECKPOINT: mark_step_failed (non-success result) ─────────────────
        checkpoint = _CP_MARK_FAILED
        mark_step_failed(db=db, step_execution=step_execution, error=str(result))

        trace_service.record_action_failed(
            db=db,
            workflow_execution=workflow_execution,
            step_execution=step_execution,
            action_name=action,
            error=str(result),
        )
        trace_service.record_step_failed(
            db=db,
            workflow_execution=workflow_execution,
            step_execution=step_execution,
            error=str(result),
        )

        logger.warning(
            "step_failed",
            extra={
                "extra_data": build_log_context(
                    workflow_execution=workflow_execution,
                    execution_step=step_execution,
                    extra={"action": action, "error": str(result)},
                )
            },
        )

        # ── CHECKPOINT: handle_retry ──────────────────────────────────────────
        checkpoint = _CP_RETRY
        retry_result = handle_retry(
            db=db,
            step_execution=step_execution,
            error=str(result),
            workflow_execution=workflow_execution,
        )

        record_retry_history(
            db=db,
            step_execution=step_execution,
            attempt_number=retry_result.get("attempts", 1),
            trigger="retry" if retry_result.get("retry_scheduled") else "dlq",
            status_at_attempt=step_execution.status,
            error=str(result),
        )

        return {"success": False, "result": result}

    except Exception as e:
        # ── DIAGNOSTIC LOG — tells you exactly where the crash happened ───────
        # checkpoint = last operation that was entered before the exception
        # This is the key field for drilling into the error
        logger.error(
            "step_execution_failed",
            extra={
                "extra_data": {
                    **build_log_context(
                        workflow_execution=workflow_execution,
                        execution_step=step_execution,
                    ),
                    # WHERE it crashed
                    "failed_at_checkpoint": checkpoint,

                    # WHAT the error is
                    "error": str(e),
                    "error_type": type(e).__name__,

                    # FULL traceback — exact line number
                    "traceback": traceback.format_exc(),

                    # WHAT was being processed
                    "step_id": step_definition.get("id", "unknown"),
                    "action": step_definition.get("action"),

                    # PAYLOAD shape — not full payload to avoid log bloat
                    "payload_keys": list(payload.keys()) if payload else [],
                    "payload_has_trace": "_trace" in (payload or {}),

                    # STEP state at time of crash
                    "step_execution_id": getattr(step_execution, "id", None),
                    "step_status": getattr(step_execution, "status", None),
                    "span_id": getattr(step_execution, "span_id", None),
                }
            },
        )

        if step_execution:
            if step_execution.status not in ("FAILED", "RETRY_SCHEDULED", "DLQ", "COMPLETED"):
                try:
                    mark_step_failed(db=db, step_execution=step_execution, error=str(e))
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
                    # Log cleanup failure separately — don't mask original error
                    logger.error(
                        "step_execution_cleanup_failed",
                        extra={
                            "extra_data": {
                                "step_execution_id": getattr(step_execution, "id", None),
                                "original_checkpoint": checkpoint,
                                "cleanup_error": str(cleanup_err),
                                "cleanup_error_type": type(cleanup_err).__name__,
                                "cleanup_traceback": traceback.format_exc(),
                            }
                        },
                    )

        return {"success": False, "error": str(e)}
