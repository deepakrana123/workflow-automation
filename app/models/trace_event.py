from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base import Base


class TraceEvent(Base):
    """
    Append-only distributed trace log.
    One row per event — never updated, never deleted.
    Query by trace_id for full workflow timeline, span_id for step timeline.
    """

    __tablename__ = "trace_events"

    id                    = Column(BigInteger, primary_key=True, index=True)
    trace_id              = Column(String(100), nullable=False, index=True)
    span_id               = Column(String(100), nullable=True, index=True)
    parent_span_id        = Column(String(100), nullable=True)
    workflow_execution_id = Column(BigInteger, ForeignKey("workflow_executions.id"), nullable=False, index=True)
    execution_step_id     = Column(BigInteger, ForeignKey("execution_steps.id"), nullable=True, index=True)

    event_type   = Column(String(100), nullable=False, index=True)
    event_source = Column(String(100), nullable=True)
    status       = Column(String(50), nullable=True)
    message      = Column(Text, nullable=True)
    payload      = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
