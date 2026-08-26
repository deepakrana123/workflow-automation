"""
app/repositories/human_task_repo.py

Persistence helpers for HumanTask rows.

Kept deliberately thin: create a pending task when a step suspends, look
tasks up, resolve them (approve/reject), and sweep timed-out ones.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.human_task import HumanTask

STATUS_PENDING = "PENDING"
STATUS_APPROVED = "APPROVED"
STATUS_REJECTED = "REJECTED"

DECISION_APPROVE = "approve"
DECISION_REJECT = "reject"

RESOLVED_BY_HUMAN = "human"
RESOLVED_BY_TIMEOUT = "timeout"

_DECISION_TO_STATUS = {
    DECISION_APPROVE: STATUS_APPROVED,
    DECISION_REJECT: STATUS_REJECTED,
}


def create_human_task(
    db: Session,
    *,
    workflow_execution_id: int,
    step_execution_id: int,
    step_id: str,
    prompt: str | None,
    on_timeout: str | None,
    timeout_seconds: int | None,
    allowed_roles: list | None = None,
    escalation_policy: dict | None = None,
) -> HumanTask:
    """Create a PENDING human task for a suspended step."""
    timeout_at = None
    if timeout_seconds:
        timeout_at = datetime.now(timezone.utc) + timedelta(seconds=timeout_seconds)

    task = HumanTask(
        workflow_execution_id=workflow_execution_id,
        step_execution_id=step_execution_id,
        step_id=step_id,
        prompt=prompt,
        status=STATUS_PENDING,
        on_timeout=on_timeout,
        timeout_at=timeout_at,
        allowed_roles=allowed_roles or [],
        escalation_policy=escalation_policy,
        escalation_level=0,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_by_id(db: Session, task_id: int) -> HumanTask | None:
    return db.query(HumanTask).filter(HumanTask.id == task_id).first()


def list_tasks(
    db: Session,
    *,
    status: str | None = None,
    workflow_execution_id: int | None = None,
) -> list[HumanTask]:
    query = db.query(HumanTask)
    if status:
        query = query.filter(HumanTask.status == status)
    if workflow_execution_id is not None:
        query = query.filter(
            HumanTask.workflow_execution_id == workflow_execution_id
        )
    return query.order_by(HumanTask.created_at.desc()).all()


def resolve(
    db: Session,
    task: HumanTask,
    *,
    decision: str,
    resolved_by: str,
) -> HumanTask:
    """Mark a task APPROVED/REJECTED. Idempotent guard is the caller's job."""
    task.status = _DECISION_TO_STATUS[decision]
    task.decision = decision
    task.resolved_by = resolved_by
    task.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return task


def get_timed_out_pending(db: Session) -> list[HumanTask]:
    """Return PENDING tasks whose timeout_at has passed."""
    now = datetime.now(timezone.utc)
    return (
        db.query(HumanTask)
        .filter(
            HumanTask.status == STATUS_PENDING,
            HumanTask.timeout_at.isnot(None),
            HumanTask.timeout_at <= now,
        )
        .all()
    )
