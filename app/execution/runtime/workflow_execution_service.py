from sqlalchemy.sql import func
from app.models.workflow_execution import WorkflowExecution
from app.core.tracing import generate_trace_id

from app.execution.runtime.constants import (
    WORKFLOW_STATUS_PENDING,
    WORKFLOW_STATUS_RUNNING,
    WORKFLOW_STATUS_COMPLETED,
    WORKFLOW_STATUS_FAILED,
    WORKFLOW_STATUS_PAUSED,
    WORKFLOW_STATUS_WAITING_APPROVAL,
    FINAL_WORKFLOW_STATES,
)
from app.execution.runtime.execution_state_manager import validate_workflow_transition
from app.core.logger import logger
from app.core.redis_client import redis_client


def create_workflow_execution(
    db,
    workflow_id: int,
    workflow_run_id: int,
    entity_id: str = None,
    correlation_id: str = None,
):
    # Generate trace_id once — stays constant for entire workflow lifecycle
    trace_id = generate_trace_id()

    execution = WorkflowExecution(
        workflow_id=workflow_id,
        workflow_run_id=workflow_run_id,
        entity_id=entity_id,
        status=WORKFLOW_STATUS_PENDING,
        trace_id=trace_id,
        # correlation_id defaults to trace_id if no external correlation provided
        correlation_id=correlation_id or trace_id,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution


def update_workflow_status(db, workflow_execution, new_status: str, error: str = None):

    # Guard: already in a terminal state — skip silently, do not raise
    db.refresh(workflow_execution)

    current_status = workflow_execution.status

    if current_status == new_status:
        return workflow_execution

    if current_status in FINAL_WORKFLOW_STATES and current_status != new_status:
        return workflow_execution

    valid = validate_workflow_transition(
        current_status=current_status,
        new_status=new_status,
    )
    if not valid:
        raise ValueError(
            f"Invalid workflow transition: {current_status} -> {new_status}"
        )

    workflow_execution.status = new_status
    workflow_execution.updated_at = func.now()

    if new_status == WORKFLOW_STATUS_RUNNING:
        workflow_execution.started_at = func.now()

    if new_status in FINAL_WORKFLOW_STATES:
        workflow_execution.completed_at = func.now()

    if error:
        workflow_execution.last_error = error

    db.commit()
    db.refresh(workflow_execution)
    return workflow_execution


def mark_workflow_running(db, workflow_execution):
    return update_workflow_status(
        db=db,
        workflow_execution=workflow_execution,
        new_status=WORKFLOW_STATUS_RUNNING,
    )


def mark_workflow_completed(db, workflow_execution):
    redis_client.delete(f"workflow_lock:{workflow_execution.workflow_id}")
    return update_workflow_status(
        db=db,
        workflow_execution=workflow_execution,
        new_status=WORKFLOW_STATUS_COMPLETED,
    )


def mark_workflow_failed(db, workflow_execution, error: str):
    redis_client.delete(f"workflow_lock:{workflow_execution.workflow_id}")
    return update_workflow_status(
        db=db,
        workflow_execution=workflow_execution,
        new_status=WORKFLOW_STATUS_FAILED,
        error=error,
    )


def mark_workflow_paused(db, workflow_execution):
    return update_workflow_status(
        db=db,
        workflow_execution=workflow_execution,
        new_status=WORKFLOW_STATUS_PAUSED,
    )


def mark_workflow_waiting_approval(db, workflow_execution):
    return update_workflow_status(
        db=db,
        workflow_execution=workflow_execution,
        new_status=WORKFLOW_STATUS_WAITING_APPROVAL,
    )
