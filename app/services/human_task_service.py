"""
app/services/human_task_service.py

Resolve human approval tasks and resume the suspended workflow.

Approve → complete the waiting step (recording the decision in its output so
          downstream steps can read it) and re-queue the execution so the DAG
          continues from where it stopped.
Reject  → fail the waiting step and fail the workflow (the gate stops here).

Timeout is the same logic, driven by the task's configured ``on_timeout``.
"""

import json

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.redis_client import redis_client
from app.execution.constants import REDIS_EVENT_QUEUE
from app.models.execution_step import ExecutionStep
from app.models.workflow_execution import WorkflowExecution
from app.repositories import human_task_repo
from app.repositories.human_task_repo import (
    DECISION_APPROVE,
    DECISION_REJECT,
    RESOLVED_BY_HUMAN,
    RESOLVED_BY_TIMEOUT,
    STATUS_PENDING,
)
from app.execution.runtime.step_execution_service import (
    mark_step_completed,
    mark_step_failed,
)
from app.execution.runtime.workflow_execution_service import mark_workflow_failed


class HumanTaskError(Exception):
    """Base error for human task resolution."""


class TaskNotFoundError(HumanTaskError):
    pass


class TaskAlreadyResolvedError(HumanTaskError):
    pass


class InvalidDecisionError(HumanTaskError):
    pass


_VALID_DECISIONS = {DECISION_APPROVE, DECISION_REJECT}


def resolve_decision(
    db: Session,
    task_id: int,
    decision: str,
    *,
    resolved_by: str = RESOLVED_BY_HUMAN,
) -> dict:
    """Apply an approve/reject decision to a pending human task.

    Raises:
        TaskNotFoundError, TaskAlreadyResolvedError, InvalidDecisionError.
    """
    decision = str(decision).lower()
    if decision not in _VALID_DECISIONS:
        raise InvalidDecisionError(
            f"Invalid decision '{decision}'. Allowed: approve, reject."
        )

    task = human_task_repo.get_by_id(db, task_id)
    if task is None:
        raise TaskNotFoundError(f"Human task {task_id} not found.")
    if task.status != STATUS_PENDING:
        raise TaskAlreadyResolvedError(
            f"Human task {task_id} already resolved ({task.status})."
        )

    step_execution = (
        db.query(ExecutionStep)
        .filter(ExecutionStep.id == task.step_execution_id)
        .first()
    )
    workflow_execution = (
        db.query(WorkflowExecution)
        .filter(WorkflowExecution.id == task.workflow_execution_id)
        .first()
    )

    if decision == DECISION_APPROVE:
        _approve(db, task, step_execution, workflow_execution, resolved_by)
    else:
        _reject(db, task, step_execution, workflow_execution, resolved_by)

    return {
        "human_task_id": task.id,
        "decision": decision,
        "workflow_execution_id": task.workflow_execution_id,
        "status": task.status,
    }


def _approve(db, task, step_execution, workflow_execution, resolved_by):
    # Complete the waiting step, recording the decision so downstream steps
    # (and rehydrated context) can branch on it.
    mark_step_completed(
        db=db,
        step_execution=step_execution,
        output_payload={
            "success": True,
            "outputs": {
                "human_decision": DECISION_APPROVE,
                "approved": True,
                "human_task_id": task.id,
            },
        },
    )
    human_task_repo.resolve(
        db, task, decision=DECISION_APPROVE, resolved_by=resolved_by
    )

    # Re-queue: runtime_processor accepts WAITING_APPROVAL, marks the workflow
    # RUNNING, rehydrates progress, and continues from the next step.
    redis_client.lpush(
        REDIS_EVENT_QUEUE,
        json.dumps({"workflow_execution_id": workflow_execution.id}),
    )
    logger.info(
        "human_task_approved",
        extra={"extra_data": {
            "human_task_id": task.id,
            "workflow_execution_id": workflow_execution.id,
            "resolved_by": resolved_by,
        }},
    )


def _reject(db, task, step_execution, workflow_execution, resolved_by):
    mark_step_failed(
        db=db,
        step_execution=step_execution,
        error=f"Human approval rejected ({resolved_by}).",
    )
    human_task_repo.resolve(
        db, task, decision=DECISION_REJECT, resolved_by=resolved_by
    )
    # A rejected approval stops the workflow. No re-queue.
    mark_workflow_failed(
        db=db,
        workflow_execution=workflow_execution,
        error="human_approval_rejected",
    )
    logger.info(
        "human_task_rejected",
        extra={"extra_data": {
            "human_task_id": task.id,
            "workflow_execution_id": workflow_execution.id,
            "resolved_by": resolved_by,
        }},
    )


def resolve_timed_out_tasks(db: Session) -> int:
    """Auto-resolve PENDING tasks whose timeout has elapsed.

    Applies each task's configured ``on_timeout`` (approve|reject).
    Returns the number of tasks resolved. Intended to be called by the reaper.
    """
    tasks = human_task_repo.get_timed_out_pending(db)
    resolved = 0
    for task in tasks:
        decision = (task.on_timeout or DECISION_REJECT).lower()
        if decision not in _VALID_DECISIONS:
            decision = DECISION_REJECT
        try:
            resolve_decision(
                db, task.id, decision, resolved_by=RESOLVED_BY_TIMEOUT
            )
            resolved += 1
        except HumanTaskError:
            # Already resolved / vanished between query and resolve — skip.
            continue
    return resolved
