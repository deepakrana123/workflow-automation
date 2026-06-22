from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class WorkflowExecution(Base):
    """
    Runtime execution state for a single workflow run.
    One row per execution attempt — retried executions reuse the same row.
    trace_id is generated once and stays constant for the full lifecycle.
    """

    __tablename__ = "workflow_executions"

    id             = Column(BigInteger, primary_key=True, index=True)
    workflow_id    = Column(BigInteger, ForeignKey("workflows.id"), nullable=False, index=True)
    workflow_run_id= Column(BigInteger, ForeignKey("workflow_runs.id"), nullable=True, index=True)
    entity_id      = Column(String(255), nullable=True)

    status         = Column(String(50), nullable=False, index=True)
    attempts       = Column(Integer, nullable=False, default=0)
    last_error     = Column(Text, nullable=True)

    # Distributed tracing — set at creation, immutable thereafter
    trace_id       = Column(String(100), nullable=True, index=True)
    correlation_id = Column(String(100), nullable=True, index=True)

    started_at     = Column(DateTime(timezone=True), nullable=True)
    completed_at   = Column(DateTime(timezone=True), nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
