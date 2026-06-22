from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base import Base


class StepRetryHistory(Base):
    """
    Immutable retry audit trail — one row per retry attempt per step.
    Never updated after write. Used for debugging, reporting, and audit.

    trigger values:
        retry              — normal scheduled retry
        dlq                — moved to dead letter queue
        timeout_recovery   — reaper recovered a stuck RUNNING execution
        manual_resume      — operator manually resumed a paused execution
    """

    __tablename__ = "step_retry_history"

    id                    = Column(BigInteger, primary_key=True, index=True)
    step_execution_id     = Column(BigInteger, ForeignKey("execution_steps.id"), nullable=False, index=True)
    workflow_execution_id = Column(BigInteger, ForeignKey("workflow_executions.id"), nullable=False, index=True)

    attempt_number    = Column(Integer, nullable=False)
    trigger           = Column(String(50), nullable=False, index=True)
    status_at_attempt = Column(String(50), nullable=False)
    error             = Column(Text, nullable=True)
    duration_ms       = Column(Integer, nullable=True)
    result_payload    = Column(JSONB, nullable=True)

    retry_scheduled_at = Column(DateTime(timezone=True), nullable=True)
    retry_executed_at  = Column(DateTime(timezone=True), nullable=True)
    created_at         = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
