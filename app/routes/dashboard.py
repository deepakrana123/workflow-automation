"""
app/routes/dashboard.py

Aggregated stats for the frontend dashboard page.
Queries workflow, workflow_execution, and execution_step tables.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta, timezone

from app.db.session import get_db
from app.models.workflow import Workflow
from app.models.workflow_execution import WorkflowExecution
from app.models.execution_step import ExecutionStep

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    """Summary KPIs for the dashboard header cards."""
    total_workflows = db.query(Workflow).count()
    active_workflows = db.query(Workflow).filter(Workflow.status == "active").count()

    total_executions = db.query(WorkflowExecution).count()

    completed = db.query(WorkflowExecution).filter(
        WorkflowExecution.status == "COMPLETED"
    ).count()

    failed = db.query(WorkflowExecution).filter(
        WorkflowExecution.status.in_(["FAILED", "DLQ"])
    ).count()

    running = db.query(WorkflowExecution).filter(
        WorkflowExecution.status.in_(["PENDING", "RUNNING"])
    ).count()

    retry_count = db.query(func.sum(WorkflowExecution.attempts)).scalar() or 0

    success_rate = round(completed / total_executions, 3) if total_executions > 0 else 0

    return {
        "total_workflows": total_workflows,
        "active_workflows": active_workflows,
        "executions_today": total_executions,
        "total_executions": total_executions,
        "completed_executions": completed,
        "failed_executions": failed,
        "success_rate": success_rate,
        "queue_depth": running,
        "retry_count": int(retry_count),
    }


@router.get("/execution-trend")
def execution_trend(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """Daily execution counts for the trend chart."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    rows = (
        db.query(
            func.date_trunc("day", WorkflowExecution.created_at).label("day"),
            func.count(WorkflowExecution.id).label("total"),
            func.sum(case((WorkflowExecution.status == "COMPLETED", 1), else_=0)).label("success"),
            func.sum(case((WorkflowExecution.status.in_(["FAILED", "DLQ"]), 1), else_=0)).label("failed"),
        )
        .filter(WorkflowExecution.created_at >= since)
        .group_by("day")
        .order_by("day")
        .all()
    )

    return [
        {
            "date": row.day.strftime("%Y-%m-%d") if row.day else "",
            "total": row.total,
            "success": row.success or 0,
            "failed": row.failed or 0,
        }
        for row in rows
    ]


@router.get("/workflow-usage")
def workflow_usage(db: Session = Depends(get_db)):
    """Top workflows by execution count."""
    rows = (
        db.query(
            Workflow.name,
            func.count(WorkflowExecution.id).label("executions"),
        )
        .join(WorkflowExecution, WorkflowExecution.workflow_id == Workflow.id, isouter=True)
        .group_by(Workflow.id, Workflow.name)
        .order_by(func.count(WorkflowExecution.id).desc())
        .limit(10)
        .all()
    )

    return [{"name": r.name, "executions": r.executions or 0} for r in rows]


@router.get("/domain-distribution")
def domain_distribution(db: Session = Depends(get_db)):
    """Workflow count per domain."""
    rows = (
        db.query(Workflow.domain, func.count(Workflow.id).label("count"))
        .group_by(Workflow.domain)
        .order_by(func.count(Workflow.id).desc())
        .all()
    )

    return [{"domain": r.domain, "count": r.count} for r in rows]
