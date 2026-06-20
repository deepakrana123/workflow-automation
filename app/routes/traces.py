"""
app/routes/traces.py

Exposes trace_events as a LangSmith-style trace viewer for the frontend.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.trace_event import TraceEvent
from app.models.workflow_execution import WorkflowExecution

router = APIRouter(prefix="/traces", tags=["traces"])


def _serialize_trace_event(e: TraceEvent) -> dict:
    return {
        "id": str(e.id),
        "trace_id": e.trace_id,
        "span_id": e.span_id,
        "parent_span_id": e.parent_span_id,
        "workflow_id": str(e.workflow_execution_id),
        "execution_id": str(e.workflow_execution_id),
        "step_id": str(e.execution_step_id) if e.execution_step_id else "",
        "event_type": e.event_type,
        "event_source": e.event_source,
        "status": (e.status or "").lower(),
        "message": e.message,
        "latency_ms": 0,
        "input": e.payload if e.event_type and "dispatched" in e.event_type.lower() else None,
        "output": e.payload if e.event_type and "success" in e.event_type.lower() else None,
        "metadata": {
            "event_type": e.event_type,
            "event_source": e.event_source,
            "trace_id": e.trace_id,
            "span_id": e.span_id,
        },
        "timing": {
            "queue_time_ms": 0,
            "processing_time_ms": 0,
            "total_time_ms": 0,
        },
        "retry_history": [],
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


@router.get("/")
def list_traces(
    workflow_id: str | None = Query(None),
    execution_id: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(TraceEvent)

    if execution_id:
        try:
            q = q.filter(TraceEvent.workflow_execution_id == int(execution_id))
        except ValueError:
            pass

    if status:
        q = q.filter(TraceEvent.status.ilike(status))

    q = q.order_by(TraceEvent.created_at.desc())
    total = q.count()
    events = q.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "data": [_serialize_trace_event(e) for e in events],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get("/{trace_id}")
def get_trace(trace_id: str, db: Session = Depends(get_db)):
    """Get a single trace event by ID, or all events for a trace_id."""
    # Try numeric ID first
    try:
        event_id = int(trace_id)
        event = db.query(TraceEvent).filter(TraceEvent.id == event_id).first()
        if event:
            return _serialize_trace_event(event)
    except ValueError:
        pass

    # Fall back to trace_id string lookup — return first match
    event = db.query(TraceEvent).filter(TraceEvent.trace_id == trace_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Trace not found")
    return _serialize_trace_event(event)
