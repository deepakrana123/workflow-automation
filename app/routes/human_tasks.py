"""
app/routes/human_tasks.py

Human approval endpoints: list pending tasks and submit a decision.

Role enforcement:
  POST /{task_id}/decision accepts an optional `actor_role` query param.
  If the task has allowed_roles configured, actor_role must be present in
  that list — otherwise 403 is returned.
  Omit actor_role only for tasks with no role restriction.

Escalation:
  Driven by the reaper worker — no route needed. The task's allowed_roles
  and escalation_level fields reflect the current escalation state and are
  included in every serialized response.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import human_task_repo
from app.services import human_task_service

router = APIRouter(prefix="/human-tasks", tags=["human-tasks"])


class DecisionRequest(BaseModel):
    decision: str  # "approve" | "reject"


def _serialize(task) -> dict:
    return {
        "id":                     task.id,
        "workflow_execution_id":  task.workflow_execution_id,
        "step_id":                task.step_id,
        "prompt":                 task.prompt,
        "status":                 task.status,
        "decision":               task.decision,
        "on_timeout":             task.on_timeout,
        "timeout_at":             task.timeout_at,
        "resolved_by":            task.resolved_by,
        "resolved_at":            task.resolved_at,
        "created_at":             task.created_at,
        # Role / escalation fields
        "allowed_roles":          task.allowed_roles or [],
        "escalation_level":       task.escalation_level or 0,
        "escalation_policy":      task.escalation_policy or {},
    }


@router.get("")
def list_human_tasks(
    status: str | None = None,
    workflow_execution_id: int | None = None,
    db: Session = Depends(get_db),
):
    """List human tasks, optionally filtered by status or execution."""
    tasks = human_task_repo.list_tasks(
        db, status=status, workflow_execution_id=workflow_execution_id
    )
    return [_serialize(t) for t in tasks]


@router.get("/{task_id}")
def get_human_task(task_id: int, db: Session = Depends(get_db)):
    task = human_task_repo.get_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Human task not found.")
    return _serialize(task)


@router.post("/{task_id}/decision")
def decide_human_task(
    task_id: int,
    body: DecisionRequest,
    actor_role: str | None = Query(
        default=None,
        description=(
            "Role of the person making the decision. Required when the task "
            "has allowed_roles configured. Omit for open tasks."
        ),
    ),
    db: Session = Depends(get_db),
):
    """
    Approve or reject a pending human task, resuming the workflow.

    Pass ?actor_role=branch_manager (or whichever role applies).
    Returns 403 if the role is not permitted for this task.
    """
    try:
        return human_task_service.resolve_decision(
            db,
            task_id,
            body.decision,
            actor_role=actor_role,
        )
    except human_task_service.TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except human_task_service.TaskAlreadyResolvedError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except human_task_service.InvalidDecisionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except human_task_service.RoleNotPermittedError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
