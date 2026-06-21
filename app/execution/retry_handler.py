from app.execution.retry_policy import should_retry
from app.execution.retry import handle_retry_event, handle_dlq_event
from app.execution.state_manager import mark_retry_scheduled, mark_dlq
from app.core.logger import logger


def handle_retry(db, step_execution, error, workflow_execution=None, skip_retry: bool = False):
    """
    Decide retry vs DLQ for a failed step.
    skip_retry=True forces immediate DLQ — used for unrecoverable errors
    like unknown_action where retrying will never succeed.
    """
    attempts = (step_execution.attempts or 0) + 1

    if not skip_retry and should_retry(attempts):
        retry_result = handle_retry_event(
            step_execution=step_execution,
            attempts=attempts,
            error=str(error),
        )

        mark_retry_scheduled(
            db=db,
            step_execution=step_execution,
            attempts=attempts,
        )

        # Emit trace event if workflow_execution context available
        if workflow_execution is not None:
            try:
                from app.services import trace_service
                trace_service.record_retry_scheduled(
                    db=db,
                    workflow_execution=workflow_execution,
                    step_execution=step_execution,
                    attempt=attempts,
                    retry_at=retry_result.get("retry_at") if retry_result else None,
                )
            except Exception as trace_err:
                logger.error(
                    "trace_retry_scheduled_failed",
                    extra={"extra_data": {"error": str(trace_err)}},
                )

        logger.warning(
            "retry_scheduled",
            extra={
                "extra_data": {
                    "step_execution_id": step_execution.id,
                    "step_name": step_execution.step_name,
                    "span_id": getattr(step_execution, "span_id", None),
                    "trace_id": getattr(workflow_execution, "trace_id", None) if workflow_execution else None,
                    "attempt": attempts,
                    "error": str(error),
                }
            },
        )

        return {"retry_scheduled": True, "attempts": attempts}

    # DLQ path — exhausted all retries
    handle_dlq_event(
        step_execution=step_execution,
        attempts=attempts,
        error=str(error),
    )

    mark_dlq(
        db=db,
        step_execution=step_execution,
        attempts=attempts,
    )

    logger.error(
        "moved_to_dlq",
        extra={
            "extra_data": {
                "step_execution_id": step_execution.id,
                "step_name": step_execution.step_name,
                "span_id": getattr(step_execution, "span_id", None),
                "trace_id": getattr(workflow_execution, "trace_id", None) if workflow_execution else None,
                "attempts": attempts,
                "error": str(error),
            }
        },
    )

    return {"retry_scheduled": False, "moved_to_dlq": True, "attempts": attempts}
