"""
app/routes/analytics.py

Deep analytics endpoints for the frontend analytics page.
Aggregates from workflow_executions, execution_steps, generation_logs,
trigger_definitions, and action_definitions.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta, timezone

from app.db.session import get_db
from app.models.workflow import Workflow
from app.models.workflow_execution import WorkflowExecution
from app.models.execution_step import ExecutionStep
from app.models.trigger_definitions import TriggerDefinition
from app.models.action_definitions import ActionDefinition

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _parse_date(date_str: str | None):
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        return None


@router.get("/workflow-creation")
def workflow_creation_trend(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    domain: str | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(
        func.date_trunc("day", Workflow.created_at).label("day"),
        func.count(Workflow.id).label("value"),
    )
    if domain:
        q = q.filter(Workflow.domain == domain)
    since = _parse_date(start_date) or (datetime.now(timezone.utc) - timedelta(days=30))
    q = q.filter(Workflow.created_at >= since)
    if end_date:
        q = q.filter(Workflow.created_at <= _parse_date(end_date))

    rows = q.group_by("day").order_by("day").all()
    return [{"date": r.day.strftime("%Y-%m-%d"), "value": r.value} for r in rows if r.day]


@router.get("/execution-volume")
def execution_volume(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    domain: str | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(
        func.date_trunc("day", WorkflowExecution.created_at).label("day"),
        func.count(WorkflowExecution.id).label("value"),
    )
    since = _parse_date(start_date) or (datetime.now(timezone.utc) - timedelta(days=30))
    q = q.filter(WorkflowExecution.created_at >= since)
    if end_date:
        q = q.filter(WorkflowExecution.created_at <= _parse_date(end_date))

    rows = q.group_by("day").order_by("day").all()
    return [{"date": r.day.strftime("%Y-%m-%d"), "value": r.value} for r in rows if r.day]


@router.get("/failures")
def failure_analysis(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    domain: str | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(
        func.date_trunc("day", WorkflowExecution.created_at).label("day"),
        func.count(WorkflowExecution.id).label("total"),
        func.sum(
            case((WorkflowExecution.status.in_(["FAILED", "DLQ"]), 1), else_=0)
        ).label("failures"),
    )
    since = _parse_date(start_date) or (datetime.now(timezone.utc) - timedelta(days=30))
    q = q.filter(WorkflowExecution.created_at >= since)
    if end_date:
        q = q.filter(WorkflowExecution.created_at <= _parse_date(end_date))

    rows = q.group_by("day").order_by("day").all()
    return [
        {
            "date": r.day.strftime("%Y-%m-%d"),
            "total": r.total,
            "failures": int(r.failures or 0),
            "rate": round(int(r.failures or 0) / r.total, 3) if r.total else 0,
        }
        for r in rows if r.day
    ]


@router.get("/retries")
def retry_analysis(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    domain: str | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(
        func.date_trunc("day", WorkflowExecution.created_at).label("day"),
        func.sum(WorkflowExecution.attempts).label("retries"),
        func.avg(WorkflowExecution.attempts).label("avg_retry_count"),
    )
    since = _parse_date(start_date) or (datetime.now(timezone.utc) - timedelta(days=30))
    q = q.filter(WorkflowExecution.created_at >= since)
    if end_date:
        q = q.filter(WorkflowExecution.created_at <= _parse_date(end_date))

    rows = q.group_by("day").order_by("day").all()
    return [
        {
            "date": r.day.strftime("%Y-%m-%d"),
            "retries": int(r.retries or 0),
            "avg_retry_count": round(float(r.avg_retry_count or 0), 2),
        }
        for r in rows if r.day
    ]


@router.get("/trigger-frequency")
def trigger_frequency(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    domain: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Count execution steps by trigger name (step_name for trigger-type steps)."""
    rows = (
        db.query(TriggerDefinition.name, TriggerDefinition.display_name)
        .filter(TriggerDefinition.active == True)
        .order_by(TriggerDefinition.name)
        .all()
    )
    # For now return catalog-level data with zero counts
    # (step-level trigger tracking requires step_type='trigger' filtering)
    return [{"name": r.display_name or r.name, "count": 0} for r in rows]


@router.get("/action-frequency")
def action_frequency(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    domain: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Count execution steps by action name."""
    rows = (
        db.query(
            ExecutionStep.step_name,
            func.count(ExecutionStep.id).label("count"),
        )
        .group_by(ExecutionStep.step_name)
        .order_by(func.count(ExecutionStep.id).desc())
        .limit(20)
        .all()
    )
    return [{"name": r.step_name, "count": r.count} for r in rows]


@router.get("")
def analytics_all(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    domain: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Convenience endpoint that returns all analytics in one call."""
    return {
        "workflow_creation_trend": workflow_creation_trend(start_date, end_date, domain, db),
        "execution_volume": execution_volume(start_date, end_date, domain, db),
        "failure_analysis": failure_analysis(start_date, end_date, domain, db),
        "retry_analysis": retry_analysis(start_date, end_date, domain, db),
        "trigger_frequency": trigger_frequency(start_date, end_date, domain, db),
        "action_frequency": action_frequency(start_date, end_date, domain, db),
    }
