from sqlalchemy.sql import func
from app.models.execution_step import ExecutionStep
from app.execution.runtime.constants import (
    STEP_STATUS_PENDING,
    STEP_STATUS_RUNNING,
    STEP_STATUS_COMPLETED,
    STEP_STATUS_FAILED,
    STEP_STATUS_WAITING,
    STEP_STATUS_SKIPPED,
    STEP_STATUS_BLOCKED,
    FINAL_STEP_STATES,
)

from app.core.logger import logger

from app.execution.runtime.execution_state_manager import validate_step_transition


def create_step_execution(
    db,
    workflow_execution_id: int,
    step_name: str,
    step_id: str,
    span_id: str = None,
    parent_span_id: str = None,
    input_payload: dict = None,
):
    step = ExecutionStep(
        workflow_execution_id=workflow_execution_id,
        step_name=step_name,
        step_id=step_id,
        span_id=span_id,
        parent_span_id=parent_span_id,
        status=STEP_STATUS_PENDING,
        input_payload=input_payload,
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


def update_step_status(
    db,
    step_execution,
    new_status: str,
    output_payload: dict = None,
    error: str = None,
):
    db.refresh(step_execution)

    current_status = step_execution.status

    if current_status == new_status:
        logger.info(
            "step",
            extra={
                "extra_data": {
                    "workflow_execution_id": step_execution.id,
                    "status": current_status,
                }
            },
        )
        return step_execution

    if current_status in FINAL_STEP_STATES and current_status != new_status:
        return step_execution
    valid = validate_step_transition(
        current_status=current_status,
        new_status=new_status,
    )

    if not valid:
        raise Exception(f"Invalid step transition: {current_status} -> {new_status}")

    step_execution.status = new_status
    step_execution.updated_at = func.now()

    if new_status == STEP_STATUS_RUNNING:
        step_execution.started_at = func.now()

    if new_status in FINAL_STEP_STATES:
        step_execution.completed_at = func.now()

    if output_payload:
        step_execution.output_payload = output_payload

    if error:
        step_execution.last_error = str(error)

    db.commit()
    db.refresh(step_execution)
    return step_execution


def mark_step_running(db, step_execution):
    return update_step_status(
        db=db, step_execution=step_execution, new_status=STEP_STATUS_RUNNING
    )


def mark_step_completed(db, step_execution, output_payload: dict = None):
    return update_step_status(
        db=db,
        step_execution=step_execution,
        new_status=STEP_STATUS_COMPLETED,
        output_payload=output_payload,
    )


def mark_step_failed(
    db,
    step_execution,
    error: str,
):
    return update_step_status(
        db=db,
        step_execution=step_execution,
        new_status=STEP_STATUS_FAILED,
        error=error,
    )


def mark_step_waiting(db, step_execution):
    return update_step_status(
        db=db,
        step_execution=step_execution,
        new_status=STEP_STATUS_WAITING,
    )


def mark_step_skipped(db, step_execution):
    return update_step_status(
        db=db,
        step_execution=step_execution,
        new_status=STEP_STATUS_SKIPPED,
    )


def mark_step_blocked(db, step_execution):
    return update_step_status(
        db=db,
        step_execution=step_execution,
        new_status=STEP_STATUS_BLOCKED,
    )
