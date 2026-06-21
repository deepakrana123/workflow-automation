"""
app/routes/executions.py

Exposes workflow execution history and step details for the frontend.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.session import get_db
from app.models.workflow_execution import WorkflowExecution
from app.models.execution_step import ExecutionStep
from app.models.workflow import Workflow

router = APIRouter(prefix="/executions", tags=["executions"])


def _serialize_step(s: ExecutionStep) -> dict:
    duration_ms = None
    if s.started_at and s.completed_at:
        duration_ms = int((s.completed_at - s.started_at).total_seconds() * 1000)

    return {
        "id": str(s.id),
        "name": s.step_name,
        "status": s.status.lower() if s.status else "unknown",
        "start_time": s.started_at.isoformat() if s.started_at else None,
        "end_time": s.completed_at.isoformat() if s.completed_at else None,
        "duration_ms": duration_ms,
        "input": s.input_payload,
        "output": s.output_payload,
        "error": s.last_error,
        "retry_count": s.attempts or 0,
    }


def _serialize_execution(e: WorkflowExecution, workflow_name: str = "", steps: list = None) -> dict:
    duration_ms = None
    if e.started_at and e.completed_at:
        duration_ms = int((e.completed_at - e.started_at).total_seconds() * 1000)

    return {
        "id": str(e.id),
        "workflow_id": str(e.workflow_id),
        "workflow_name": workflow_name,
        "status": e.status.lower() if e.status else "unknown",
        "start_time": e.started_at.isoformat() if e.started_at else (e.created_at.isoformat() if e.created_at else None),
        "end_time": e.completed_at.isoformat() if e.completed_at else None,
        "duration_ms": duration_ms,
        "retry_count": e.attempts or 0,
        "error": e.last_error,
        "trace_id": e.trace_id,
        "steps": steps or [],
    }


@router.get("/")
def list_executions(
    workflow_id: str | None = Query(None),
    status: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(WorkflowExecution)

    if workflow_id:
        try:
            q = q.filter(WorkflowExecution.workflow_id == int(workflow_id))
        except ValueError:
            pass

    if status and status != "all":
        q = q.filter(WorkflowExecution.status.ilike(status))

    if start_date:
        q = q.filter(WorkflowExecution.created_at >= start_date)
    if end_date:
        q = q.filter(WorkflowExecution.created_at <= end_date)

    q = q.order_by(WorkflowExecution.created_at.desc())
    total = q.count()
    executions = q.offset((page - 1) * page_size).limit(page_size).all()

    # Batch load workflow names
    workflow_ids = list({e.workflow_id for e in executions})
    workflows = {}
    if workflow_ids:
        wf_rows = db.query(Workflow).filter(Workflow.id.in_(workflow_ids)).all()
        workflows = {w.id: w.name for w in wf_rows}

    data = [
        _serialize_execution(e, workflow_name=workflows.get(e.workflow_id, ""))
        for e in executions
    ]

    return {
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get("/{execution_id}")
def get_execution(execution_id: int, db: Session = Depends(get_db)):
    execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.id == execution_id
    ).first()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    workflow = db.query(Workflow).filter(Workflow.id == execution.workflow_id).first()
    workflow_name = workflow.name if workflow else ""

    steps = db.query(ExecutionStep).filter(
        ExecutionStep.workflow_execution_id == execution_id
    ).order_by(ExecutionStep.created_at).all()

    return _serialize_execution(
        execution,
        workflow_name=workflow_name,
        steps=[_serialize_step(s) for s in steps],
    )
