from app.execution.runtime.workflow_execution_service import (
    mark_workflow_completed,
    mark_workflow_failed,
    mark_workflow_waiting_approval,
)
from app.execution.runtime.step_execution_service import get_step_statuses
from app.execution.runtime.constants import (
    STEP_STATUS_COMPLETED,
    STEP_STATUS_FAILED,
    STEP_STATUS_WAITING,
    STEP_STATUS_DLQ,
    STEP_STATUS_RETRY_SCHEDULED,
)
from app.services import trace_service
from app.core.tracing import build_log_context
from app.core.logger import logger

# Step status values that indicate non-final retry state
_STEP_STATUS_DLQ = "DLQ"
_STEP_STATUS_RETRY_SCHEDULED = "RETRY_SCHEDULED"


def finalize_workflow_execution(db, workflow_execution):
    statuses = get_step_statuses(db, workflow_execution.id)

    # DLQ — permanent failure
    if any(status == STEP_STATUS_DLQ for status in statuses):
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
    if any(status == STEP_STATUS_RETRY_SCHEDULED for status in statuses):
        logger.info(
            "workflow_finalization_deferred_retry_pending",
            extra={"extra_data": build_log_context(workflow_execution=workflow_execution)},
        )
        return

    # All steps completed
    if all(status == STEP_STATUS_COMPLETED for status in statuses):
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
    if any(status == STEP_STATUS_FAILED for status in statuses):
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
    if any(status == STEP_STATUS_WAITING for status in statuses):
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
