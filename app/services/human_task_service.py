"""
app/services/human_task_service.py

Resolve human approval tasks and resume the suspended workflow.

Approve → complete the waiting step (recording the decision in its output so
          downstream steps can read it) and re-queue the execution so the DAG
          continues from where it stopped.
Reject  → fail the waiting step and fail the workflow (the gate stops here).

Role enforcement:
  If allowed_roles is non-empty, the caller must supply an actor_role that
  is present in that list. Otherwise RoleNotPermittedError (403) is raised.
  Empty allowed_roles means anyone can resolve.

Escalation (reaper-driven):
  When a task times out and escalation_policy is configured, the reaper
  calls escalate_timed_out_tasks() instead of auto-resolving.
  Resolution order per timed-out task:
    1. If escalation_policy exists AND escalation_level < max_escalation_levels:
         escalate → bump level, switch allowed_roles, reset timeout_at.
    2. Otherwise: auto-resolve via on_timeout (approve|reject).
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


# ── Errors ────────────────────────────────────────────────────────────────────

class HumanTaskError(Exception):
    """Base error for human task resolution."""


class TaskNotFoundError(HumanTaskError):
    pass


class TaskAlreadyResolvedError(HumanTaskError):
    pass


class InvalidDecisionError(HumanTaskError):
    pass


class RoleNotPermittedError(HumanTaskError):
    """Raised when the actor's role is not in the task's allowed_roles."""


_VALID_DECISIONS = {DECISION_APPROVE, DECISION_REJECT}


# ── Public API ────────────────────────────────────────────────────────────────

def resolve_decision(
    db: Session,
    task_id: int,
    decision: str,
    *,
    resolved_by: str = RESOLVED_BY_HUMAN,
    actor_role: str | None = None,
) -> dict:
    """
    Apply an approve/reject decision to a pending human task.

    actor_role  — the role of the person making the decision.
                  Required when the task has allowed_roles configured.
                  Ignored when allowed_roles is empty (open task).

    Raises:
        TaskNotFoundError       — task does not exist
        TaskAlreadyResolvedError — task is not PENDING
        InvalidDecisionError    — decision is not approve/reject
        RoleNotPermittedError   — actor_role not in allowed_roles
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

    # ── Role enforcement ──────────────────────────────────────────────────────
    allowed = task.allowed_roles or []
    if allowed:
        if not actor_role or actor_role not in allowed:
            raise RoleNotPermittedError(
                f"Role '{actor_role}' is not permitted to resolve task {task_id}. "
                f"Allowed roles: {allowed}."
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
        "human_task_id":        task.id,
        "decision":             decision,
        "workflow_execution_id": task.workflow_execution_id,
        "status":               task.status,
    }


def handle_timed_out_tasks(db: Session) -> dict:
    """
    Process all PENDING tasks whose timeout_at has elapsed.

    For each task:
      - If escalation_policy is set AND current level < max_escalation_levels:
          escalate — bump level, switch allowed_roles, reset timeout_at.
      - Otherwise: auto-resolve via on_timeout (approve|reject).

    Returns {escalated: int, resolved: int}.
    Called by the reaper worker.
    """
    tasks = human_task_repo.get_timed_out_pending(db)
    escalated = 0
    resolved  = 0

    for task in tasks:
        policy = task.escalation_policy or {}
        max_levels    = int(policy.get("max_escalation_levels", 0))
        current_level = task.escalation_level or 0

        if policy and current_level < max_levels:
            # ── Escalate ──────────────────────────────────────────────────────
            escalate_to_role  = policy.get("escalate_to_role", "")
            timeout_minutes   = int(policy.get("timeout_minutes", 60))

            if escalate_to_role:
                human_task_repo.escalate_task(
                    db,
                    task,
                    new_role=escalate_to_role,
                    timeout_minutes=timeout_minutes,
                )
                escalated += 1
                logger.info(
                    "human_task_escalated",
                    extra={"extra_data": {
                        "human_task_id":     task.id,
                        "escalation_level":  task.escalation_level,
                        "escalated_to_role": escalate_to_role,
                        "timeout_minutes":   timeout_minutes,
                    }},
                )
                continue  # do NOT auto-resolve yet — give the new role a chance

        # ── Auto-resolve ──────────────────────────────────────────────────────
        decision = (task.on_timeout or DECISION_REJECT).lower()
        if decision not in _VALID_DECISIONS:
            decision = DECISION_REJECT

        try:
            resolve_decision(
                db,
                task.id,
                decision,
                resolved_by=RESOLVED_BY_TIMEOUT,
                # Bypass role check for timeout auto-resolution — the reaper
                # acts with system authority regardless of allowed_roles.
                actor_role=None,
            )
            resolved += 1
        except HumanTaskError:
            # Already resolved / vanished between query and resolve — skip.
            continue

    return {"escalated": escalated, "resolved": resolved}


# ── Kept for backward-compat (reaper currently calls this name) ───────────────

def resolve_timed_out_tasks(db: Session) -> int:
    """Backward-compatible wrapper — delegates to handle_timed_out_tasks."""
    result = handle_timed_out_tasks(db)
    return result["escalated"] + result["resolved"]


# ── Private helpers ───────────────────────────────────────────────────────────

def _approve(db, task, step_execution, workflow_execution, resolved_by):
    mark_step_completed(
        db=db,
        step_execution=step_execution,
        output_payload={
            "success": True,
            "outputs": {
                "human_decision": DECISION_APPROVE,
                "approved":       True,
                "human_task_id":  task.id,
            },
        },
    )
    human_task_repo.resolve(
        db, task, decision=DECISION_APPROVE, resolved_by=resolved_by
    )
    redis_client.lpush(
        REDIS_EVENT_QUEUE,
        json.dumps({"workflow_execution_id": workflow_execution.id}),
    )
    logger.info(
        "human_task_approved",
        extra={"extra_data": {
            "human_task_id":        task.id,
            "workflow_execution_id": workflow_execution.id,
            "resolved_by":          resolved_by,
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
    mark_workflow_failed(
        db=db,
        workflow_execution=workflow_execution,
        error="human_approval_rejected",
    )
    logger.info(
        "human_task_rejected",
        extra={"extra_data": {
            "human_task_id":        task.id,
            "workflow_execution_id": workflow_execution.id,
            "resolved_by":          resolved_by,
        }},
    )
