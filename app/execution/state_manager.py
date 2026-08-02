"""
app/execution/state_manager.py

Low-level step status mutations via direct SQL update.
Used by retry_handler for atomic RETRY_SCHEDULED and DLQ transitions.
"""

from app.models.execution_step import ExecutionStep
from app.execution.runtime.constants import STEP_STATUS_RETRY_SCHEDULED, STEP_STATUS_DLQ
from sqlalchemy.orm import Session
from sqlalchemy.sql import func


def mark_retry_scheduled(db: Session, step_execution, attempts: int) -> None:
    db.query(ExecutionStep).filter(ExecutionStep.id == step_execution.id).update(
        {
            "status": STEP_STATUS_RETRY_SCHEDULED,
            "attempts": attempts,
            "updated_at": func.now(),
        }
    )
    db.commit()


def mark_dlq(db: Session, step_execution, attempts: int) -> None:
    db.query(ExecutionStep).filter(ExecutionStep.id == step_execution.id).update(
        {
            "status": STEP_STATUS_DLQ,
            "attempts": attempts,
            "updated_at": func.now(),
        }
    )
    db.commit()
