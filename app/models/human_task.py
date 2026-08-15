from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.db.base import Base


class HumanTask(Base):
    """
    A pending human decision on a suspended workflow step.

    Created when a ``human_task`` step suspends the DAG. An operator resolves
    it with Approve or Reject; a reaper may auto-resolve it on timeout using
    ``on_timeout``.

    MVP scope — no roles, assignees, escalation, delegation or SLA.

    status:   PENDING | APPROVED | REJECTED
    decision: approve | reject   (set when resolved)
    resolved_by: "human" | "timeout"
    """

    __tablename__ = "human_tasks"

    id                    = Column(BigInteger, primary_key=True, index=True)
    workflow_execution_id = Column(
        BigInteger, ForeignKey("workflow_executions.id"), nullable=False, index=True
    )
    step_execution_id = Column(
        BigInteger, ForeignKey("execution_steps.id"), nullable=False, index=True
    )
    step_id = Column(String, nullable=False)

    prompt = Column(Text, nullable=True)

    status   = Column(String(20), nullable=False, default="PENDING", index=True)
    decision = Column(String(10), nullable=True)          # approve | reject

    on_timeout  = Column(String(10), nullable=True)       # approve | reject
    timeout_at  = Column(DateTime(timezone=True), nullable=True, index=True)

    resolved_by = Column(String(20), nullable=True)       # human | timeout
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
