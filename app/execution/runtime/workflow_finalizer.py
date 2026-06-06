from app.models.execution_step import ExecutionStep
from app.execution.runtime.workflow_execution_service import (
    mark_workflow_completed,
    mark_workflow_failed,
    mark_workflow_waiting_approval,
)
from app.services import trace_service
from app.core.tracing import build_log_context
from app.core.logger import logger


def finalize_workflow_execution(db, workflow_execution):
    steps = (
        db.query(ExecutionStep)
        .filter(ExecutionStep.workflow_execution_id == workflow_execution.id)
        .all()
    )

    statuses = [step.status for step in steps]

    # DLQ — permanent failure
    if any(status == "DLQ" for status in statuses):
        mark_workflow_failed(
            db=db,
            workflow_execution=workflow_execution,
            error="one_or_more_steps_moved_to_dlq",
        )
        trace_service.record_workflow_failed(
            db=db,
            workflow_execution=workflow_execution,
            error="one_or_more_steps_moved_to_dlq",
        )
        logger.error(
            "workflow_failed",
            extra={"extra_data": build_log_context(
                workflow_execution=workflow_execution,
                extra={"reason": "dlq"},
            )},
        )
        return

    # RETRY_SCHEDULED — still in progress, defer finalization
    if any(status == "RETRY_SCHEDULED" for status in statuses):
        logger.info(
            "workflow_finalization_deferred_retry_pending",
            extra={"extra_data": build_log_context(workflow_execution=workflow_execution)},
        )
        return

    # All steps completed
    if all(status == "COMPLETED" for status in statuses):
        mark_workflow_completed(db=db, workflow_execution=workflow_execution)
        trace_service.record_workflow_completed(
            db=db,
            workflow_execution=workflow_execution,
        )
        logger.info(
            "workflow_completed",
            extra={"extra_data": build_log_context(workflow_execution=workflow_execution)},
        )
        return

    # Any step failed
    if any(status == "FAILED" for status in statuses):
        mark_workflow_failed(
            db=db,
            workflow_execution=workflow_execution,
            error="one_or_more_steps_failed",
        )
        trace_service.record_workflow_failed(
            db=db,
            workflow_execution=workflow_execution,
            error="one_or_more_steps_failed",
        )
        logger.error(
            "workflow_failed",
            extra={"extra_data": build_log_context(
                workflow_execution=workflow_execution,
                extra={"reason": "step_failed"},
            )},
        )
        return

    # Waiting for approval
    if any(status == "WAITING" for status in statuses):
        mark_workflow_waiting_approval(db=db, workflow_execution=workflow_execution)
        logger.info(
            "workflow_waiting_approval",
            extra={"extra_data": build_log_context(workflow_execution=workflow_execution)},
        )
        return

    logger.info(
        "workflow_execution_still_active",
        extra={"extra_data": build_log_context(workflow_execution=workflow_execution)},
    )
