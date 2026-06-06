from datetime import datetime, timezone
from app.models.step_retry_history import StepRetryHistory
from app.core.logger import logger


def record_retry_history(
    db,
    step_execution,
    attempt_number: int,
    trigger: str,
    status_at_attempt: str,
    error: str = None,
    duration_ms: int = None,
    result_payload: dict = None,
    retry_scheduled_at: datetime = None,
):
    """
    Write an immutable retry history entry for a step execution.

    trigger values:
        "retry"            — normal retry scheduled
        "dlq"              — moved to dead letter queue
        "timeout_recovery" — reaper recovered a stuck RUNNING execution
        "manual_resume"    — operator manually resumed a paused execution
    """
    try:
        entry = StepRetryHistory(
            step_execution_id=step_execution.id,
            workflow_execution_id=step_execution.workflow_execution_id,
            attempt_number=attempt_number,
            trigger=trigger,
            status_at_attempt=status_at_attempt,
            error=str(error)[:2000] if error else None,
            duration_ms=duration_ms,
            result_payload=result_payload,
            retry_scheduled_at=retry_scheduled_at,
            retry_executed_at=datetime.now(timezone.utc),
        )
        db.add(entry)
        db.commit()

        logger.info(
            "step_retry_history_recorded",
            extra={
                "extra_data": {
                    "step_execution_id": step_execution.id,
                    "workflow_execution_id": step_execution.workflow_execution_id,
                    "attempt_number": attempt_number,
                    "trigger": trigger,
                    "status": status_at_attempt,
                }
            },
        )
        return entry

    except Exception as e:
        # Never let history writing crash the main execution path
        db.rollback()
        logger.error(
            "step_retry_history_write_failed",
            extra={
                "extra_data": {
                    "step_execution_id": step_execution.id,
                    "error": str(e),
                }
            },
        )
        return None


def get_retry_history(db, step_execution_id: int):
    """Fetch all retry history for a step, ordered by attempt number."""
    return (
        db.query(StepRetryHistory)
        .filter(StepRetryHistory.step_execution_id == step_execution_id)
        .order_by(StepRetryHistory.attempt_number)
        .all()
    )


def get_workflow_retry_history(db, workflow_execution_id: int):
    """Fetch all retry history for all steps in a workflow execution."""
    return (
        db.query(StepRetryHistory)
        .filter(StepRetryHistory.workflow_execution_id == workflow_execution_id)
        .order_by(StepRetryHistory.created_at)
        .all()
    )
