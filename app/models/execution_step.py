from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base import Base


class ExecutionStep(Base):
    """
    Per-step runtime state within a workflow execution.
    One row per step per execution — status transitions through the step state machine.
    span_id is generated at step creation and stays constant for the step lifecycle.
    """

    __tablename__ = "execution_steps"

    id                    = Column(BigInteger, primary_key=True, index=True)
    workflow_execution_id = Column(BigInteger, ForeignKey("workflow_executions.id"), nullable=False, index=True)

    step_id    = Column(String, nullable=False)
    step_name  = Column(String(255), nullable=False)
    step_type  = Column(String(50), nullable=False, default="action")
    depends_on = Column(JSONB, nullable=True)

    status   = Column(String(50), nullable=False, index=True)
    attempts = Column(Integer, nullable=False, default=0)

    # Distributed tracing
    span_id        = Column(String(100), nullable=True, index=True)
    parent_span_id = Column(String(100), nullable=True)

    input_payload  = Column(JSONB, nullable=True)
    output_payload = Column(JSONB, nullable=True)
    last_error     = Column(Text, nullable=True)

    started_at   = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
