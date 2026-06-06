"""
app/services/trace_service.py

Central trace event service.
All trace writes go through this module — never write TraceEvent directly.

Design:
- Never raises — trace failures must never crash execution
- All functions are safe to call even if trace_id/span_id are None
- Payload is always sanitized before write
"""

import json
from datetime import datetime, timezone
from app.models.trace_event import TraceEvent
from app.core.logger import logger


def _safe_payload(data: dict) -> dict | None:
    """
    Force all values in a dict to JSON-serializable primitives.
    Prevents MemoryView/ULID/SQLAlchemy instrumented attribute errors
    when psycopg2 writes to JSONB columns.
    """
    if not data:
        return None
    try:
        return json.loads(json.dumps(data, default=str))
    except Exception:
        return None


# ─────────────────────────────────────────────
# EVENT TYPE CONSTANTS
# ─────────────────────────────────────────────

class TraceEventType:
    WORKFLOW_STARTED    = "WORKFLOW_STARTED"
    WORKFLOW_COMPLETED  = "WORKFLOW_COMPLETED"
    WORKFLOW_FAILED     = "WORKFLOW_FAILED"

    STEP_STARTED        = "STEP_STARTED"
    STEP_COMPLETED      = "STEP_COMPLETED"
    STEP_FAILED         = "STEP_FAILED"

    RETRY_SCHEDULED     = "RETRY_SCHEDULED"
    RETRY_STARTED       = "RETRY_STARTED"
    RETRY_COMPLETED     = "RETRY_COMPLETED"

    REAPER_RECOVERED    = "REAPER_RECOVERED"

    ACTION_DISPATCHED   = "ACTION_DISPATCHED"
    ACTION_SUCCESS      = "ACTION_SUCCESS"
    ACTION_FAILED       = "ACTION_FAILED"


# ─────────────────────────────────────────────
# CORE WRITE
# ─────────────────────────────────────────────

def create_trace_event(
    db,
    workflow_execution_id: int,
    trace_id: str,
    event_type: str,
    event_source: str = None,
    span_id: str = None,
    parent_span_id: str = None,
    execution_step_id: int = None,
    status: str = None,
    message: str = None,
    payload: dict = None,
) -> TraceEvent | None:
    """
    Write a single trace event row.
    Returns the created event or None if write failed.
    Never raises — trace failures must not crash execution.
    """
    if not trace_id or not workflow_execution_id:
        return None

    try:
        event = TraceEvent(
            trace_id=str(trace_id),
            span_id=str(span_id) if span_id else None,
            parent_span_id=str(parent_span_id) if parent_span_id else None,
            workflow_execution_id=int(workflow_execution_id),
            execution_step_id=int(execution_step_id) if execution_step_id else None,
            event_type=str(event_type),
            event_source=str(event_source) if event_source else None,
            status=str(status) if status else None,
            message=str(message) if message else None,
            payload=_safe_payload(payload),
        )
        db.add(event)
        db.commit()
        return event

    except Exception as e:
        db.rollback()
        logger.error(
            "trace_event_write_failed",
            extra={
                "extra_data": {
                    "trace_id": trace_id,
                    "event_type": event_type,
                    "error": str(e),
                }
            },
        )
        return None


# ─────────────────────────────────────────────
# WORKFLOW EVENTS
# ─────────────────────────────────────────────

def record_workflow_started(db, workflow_execution) -> None:
    create_trace_event(
        db=db,
        workflow_execution_id=workflow_execution.id,
        trace_id=workflow_execution.trace_id,
        event_type=TraceEventType.WORKFLOW_STARTED,
        event_source="runtime_processor",
        status="pending",
        message=f"Workflow execution started",
        payload={
            "workflow_id": workflow_execution.workflow_id,
            "entity_id": workflow_execution.entity_id,
        },
    )


def record_workflow_completed(db, workflow_execution) -> None:
    create_trace_event(
        db=db,
        workflow_execution_id=workflow_execution.id,
        trace_id=workflow_execution.trace_id,
        event_type=TraceEventType.WORKFLOW_COMPLETED,
        event_source="workflow_finalizer",
        status="success",
        message="Workflow execution completed successfully",
    )


def record_workflow_failed(db, workflow_execution, error: str = None) -> None:
    create_trace_event(
        db=db,
        workflow_execution_id=workflow_execution.id,
        trace_id=workflow_execution.trace_id,
        event_type=TraceEventType.WORKFLOW_FAILED,
        event_source="workflow_finalizer",
        status="failed",
        message="Workflow execution failed",
        payload={"error": error} if error else None,
    )


# ─────────────────────────────────────────────
# STEP EVENTS
# ─────────────────────────────────────────────

def record_step_started(db, workflow_execution, step_execution) -> None:
    create_trace_event(
        db=db,
        workflow_execution_id=workflow_execution.id,
        trace_id=workflow_execution.trace_id,
        span_id=step_execution.span_id,
        parent_span_id=step_execution.parent_span_id,
        execution_step_id=step_execution.id,
        event_type=TraceEventType.STEP_STARTED,
        event_source="step_executor",
        status="pending",
        message=f"Step '{step_execution.step_name}' started",
        payload={
            "step_name": step_execution.step_name,
            "step_id": step_execution.step_id,
            "attempt": step_execution.attempts,
        },
    )


def record_step_completed(db, workflow_execution, step_execution, result: dict = None) -> None:
    create_trace_event(
        db=db,
        workflow_execution_id=workflow_execution.id,
        trace_id=workflow_execution.trace_id,
        span_id=step_execution.span_id,
        parent_span_id=step_execution.parent_span_id,
        execution_step_id=step_execution.id,
        event_type=TraceEventType.STEP_COMPLETED,
        event_source="step_executor",
        status="success",
        message=f"Step '{step_execution.step_name}' completed",
        payload={"result": result} if result else None,
    )


def record_step_failed(db, workflow_execution, step_execution, error: str = None) -> None:
    create_trace_event(
        db=db,
        workflow_execution_id=workflow_execution.id,
        trace_id=workflow_execution.trace_id,
        span_id=step_execution.span_id,
        parent_span_id=step_execution.parent_span_id,
        execution_step_id=step_execution.id,
        event_type=TraceEventType.STEP_FAILED,
        event_source="step_executor",
        status="failed",
        message=f"Step '{step_execution.step_name}' failed",
        payload={
            "error": error,
            "attempt": step_execution.attempts,
        },
    )


# ─────────────────────────────────────────────
# RETRY EVENTS
# ─────────────────────────────────────────────

def record_retry_scheduled(
    db, workflow_execution, step_execution, attempt: int, retry_at: int = None
) -> None:
    create_trace_event(
        db=db,
        workflow_execution_id=workflow_execution.id,
        trace_id=workflow_execution.trace_id,
        span_id=step_execution.span_id,
        parent_span_id=step_execution.parent_span_id,
        execution_step_id=step_execution.id,
        event_type=TraceEventType.RETRY_SCHEDULED,
        event_source="retry_handler",
        status="pending",
        message=f"Retry scheduled for step '{step_execution.step_name}' attempt {attempt}",
        payload={"attempt": attempt, "retry_at": retry_at},
    )


def record_retry_started(db, workflow_execution, step_execution, attempt: int) -> None:
    create_trace_event(
        db=db,
        workflow_execution_id=workflow_execution.id,
        trace_id=workflow_execution.trace_id,
        span_id=step_execution.span_id,
        parent_span_id=step_execution.parent_span_id,
        execution_step_id=step_execution.id,
        event_type=TraceEventType.RETRY_STARTED,
        event_source="retry_executor",
        status="pending",
        message=f"Retry started for step '{step_execution.step_name}' attempt {attempt}",
        payload={"attempt": attempt},
    )


def record_retry_completed(
    db, workflow_execution, step_execution, attempt: int, success: bool
) -> None:
    create_trace_event(
        db=db,
        workflow_execution_id=workflow_execution.id,
        trace_id=workflow_execution.trace_id,
        span_id=step_execution.span_id,
        parent_span_id=step_execution.parent_span_id,
        execution_step_id=step_execution.id,
        event_type=TraceEventType.RETRY_COMPLETED,
        event_source="retry_executor",
        status="success" if success else "failed",
        message=f"Retry {'succeeded' if success else 'failed'} for step '{step_execution.step_name}'",
        payload={"attempt": attempt, "success": success},
    )


# ─────────────────────────────────────────────
# REAPER EVENT
# ─────────────────────────────────────────────

def record_reaper_recovered(db, workflow_execution, stuck_since: str = None) -> None:
    create_trace_event(
        db=db,
        workflow_execution_id=workflow_execution.id,
        trace_id=workflow_execution.trace_id,
        event_type=TraceEventType.REAPER_RECOVERED,
        event_source="reaper_worker",
        status="failed",
        message="Reaper recovered stuck RUNNING execution",
        payload={
            "stuck_since": stuck_since,
            "attempts": workflow_execution.attempts,
        },
    )


# ─────────────────────────────────────────────
# ACTION EVENTS
# ─────────────────────────────────────────────

def record_action_dispatched(
    db, workflow_execution, step_execution, action_name: str
) -> None:
    create_trace_event(
        db=db,
        workflow_execution_id=workflow_execution.id,
        trace_id=workflow_execution.trace_id,
        span_id=step_execution.span_id,
        parent_span_id=step_execution.parent_span_id,
        execution_step_id=step_execution.id,
        event_type=TraceEventType.ACTION_DISPATCHED,
        event_source="step_executor",
        status="pending",
        message=f"Action '{action_name}' dispatched",
        payload={"action_name": action_name},
    )


def record_action_success(
    db, workflow_execution, step_execution, action_name: str, result: dict = None
) -> None:
    create_trace_event(
        db=db,
        workflow_execution_id=workflow_execution.id,
        trace_id=workflow_execution.trace_id,
        span_id=step_execution.span_id,
        parent_span_id=step_execution.parent_span_id,
        execution_step_id=step_execution.id,
        event_type=TraceEventType.ACTION_SUCCESS,
        event_source="step_executor",
        status="success",
        message=f"Action '{action_name}' succeeded",
        payload={"action_name": action_name, "result": result},
    )


def record_action_failed(
    db, workflow_execution, step_execution, action_name: str, error: str = None
) -> None:
    create_trace_event(
        db=db,
        workflow_execution_id=workflow_execution.id,
        trace_id=workflow_execution.trace_id,
        span_id=step_execution.span_id,
        parent_span_id=step_execution.parent_span_id,
        execution_step_id=step_execution.id,
        event_type=TraceEventType.ACTION_FAILED,
        event_source="step_executor",
        status="failed",
        message=f"Action '{action_name}' failed",
        payload={"action_name": action_name, "error": error},
    )


# ─────────────────────────────────────────────
# QUERY HELPERS
# ─────────────────────────────────────────────

def get_trace(db, trace_id: str) -> list:
    """Fetch full execution timeline for a trace_id, ordered by time."""
    return (
        db.query(TraceEvent)
        .filter(TraceEvent.trace_id == trace_id)
        .order_by(TraceEvent.created_at)
        .all()
    )


def get_step_trace(db, span_id: str) -> list:
    """Fetch all events for a specific step span."""
    return (
        db.query(TraceEvent)
        .filter(TraceEvent.span_id == span_id)
        .order_by(TraceEvent.created_at)
        .all()
    )


def get_workflow_execution_trace(db, workflow_execution_id: int) -> list:
    """Fetch all events for a workflow execution."""
    return (
        db.query(TraceEvent)
        .filter(TraceEvent.workflow_execution_id == workflow_execution_id)
        .order_by(TraceEvent.created_at)
        .all()
    )
