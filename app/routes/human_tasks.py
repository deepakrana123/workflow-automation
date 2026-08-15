"""
app/routes/human_tasks.py

Human approval endpoints: list pending tasks and submit a decision.

MVP scope — Approve / Reject only. No assignees, roles, or escalation.
"""

from fastapi import APIRouter, Depends, HTTPException
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
        "id": task.id,
        "workflow_execution_id": task.workflow_execution_id,
        "step_id": task.step_id,
        "prompt": task.prompt,
        "status": task.status,
        "decision": task.decision,
        "on_timeout": task.on_timeout,
        "timeout_at": task.timeout_at,
        "resolved_by": task.resolved_by,
        "resolved_at": task.resolved_at,
        "created_at": task.created_at,
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
    db: Session = Depends(get_db),
):
    """Approve or reject a pending human task, resuming the workflow."""
    try:
        return human_task_service.resolve_decision(db, task_id, body.decision)
    except human_task_service.TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except human_task_service.TaskAlreadyResolvedError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except human_task_service.InvalidDecisionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
