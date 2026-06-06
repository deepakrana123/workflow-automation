from app.execution.runtime.constants import (
    WORKFLOW_STATUS_PENDING,
    WORKFLOW_STATUS_RUNNING,
    WORKFLOW_STATUS_COMPLETED,
    WORKFLOW_STATUS_FAILED,
    WORKFLOW_STATUS_PAUSED,
    WORKFLOW_STATUS_WAITING_APPROVAL,
    STEP_STATUS_PENDING,
    STEP_STATUS_RUNNING,
    STEP_STATUS_COMPLETED,
    STEP_STATUS_FAILED,
    STEP_STATUS_SKIPPED,
    STEP_STATUS_WAITING,
    STEP_STATUS_BLOCKED,
    FINAL_WORKFLOW_STATES,
    FINAL_STEP_STATES,
)

WORKFLOW_TRANSITIONS = {
    WORKFLOW_STATUS_PENDING: {
        WORKFLOW_STATUS_RUNNING,
        WORKFLOW_STATUS_FAILED,
    },
    WORKFLOW_STATUS_RUNNING: {
        WORKFLOW_STATUS_COMPLETED,
        WORKFLOW_STATUS_FAILED,
        WORKFLOW_STATUS_PAUSED,
        WORKFLOW_STATUS_WAITING_APPROVAL,
    },
    WORKFLOW_STATUS_PAUSED: {
        WORKFLOW_STATUS_RUNNING,
        WORKFLOW_STATUS_FAILED,
    },
    WORKFLOW_STATUS_WAITING_APPROVAL: {
        WORKFLOW_STATUS_RUNNING,
        WORKFLOW_STATUS_FAILED,
    },
}


STEP_TRANSITIONS = {
    STEP_STATUS_PENDING: {
        STEP_STATUS_RUNNING,
        STEP_STATUS_SKIPPED,
        STEP_STATUS_BLOCKED,
    },
    STEP_STATUS_RUNNING: {
        STEP_STATUS_COMPLETED,
        STEP_STATUS_FAILED,
        STEP_STATUS_WAITING,
    },
    STEP_STATUS_WAITING: {
        STEP_STATUS_RUNNING,
        STEP_STATUS_FAILED,
    },
    STEP_STATUS_BLOCKED: {
        STEP_STATUS_PENDING,
        STEP_STATUS_SKIPPED,
    },
}


def can_transition(current_status: str, new_status: str, transitions: dict) -> bool:
    allowed = transitions.get(current_status, set())
    return new_status in allowed


def validate_workflow_transition(current_status: str, new_status: str) -> bool:
    # Already terminal — caller should skip, not raise
    if current_status in FINAL_WORKFLOW_STATES:
        return False
    return can_transition(
        current_status=current_status,
        new_status=new_status,
        transitions=WORKFLOW_TRANSITIONS,
    )


def validate_step_transition(current_status: str, new_status: str) -> bool:
    # Already terminal — caller should skip, not raise
    if current_status in FINAL_STEP_STATES:
        return False
    return can_transition(
        current_status=current_status,
        new_status=new_status,
        transitions=STEP_TRANSITIONS,
    )
