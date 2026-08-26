from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.db.base import Base


class HumanTask(Base):
    """
    A pending human decision on a suspended workflow step.

    Created when a ``human_task`` step suspends the DAG. An operator resolves
    it with Approve or Reject; a reaper may auto-resolve it on timeout using
    ``on_timeout``.

    status:        PENDING | APPROVED | REJECTED
    decision:      approve | reject   (set when resolved)
    resolved_by:   "human" | "timeout"

    Role-aware fields (added migration c1d2e3f4a5b6):
      allowed_roles      — JSONB list of role names that may resolve this task.
                           Populated from BusinessRuleDefinition.allowed_roles
                           at HumanTask creation. Empty list = anyone can resolve.
      escalation_policy  — JSONB: {timeout_minutes, escalate_to_role, max_escalation_levels}
      escalation_level   — current depth in the escalation chain (starts 0)
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

    # ── Role-aware fields ─────────────────────────────────────────────────────
    # List of role names that may resolve this task.
    # Example: ["branch_manager", "zone_manager"]
    allowed_roles = Column(JSONB, nullable=True, default=list)

    # Escalation config: {timeout_minutes: int, escalate_to_role: str,
    #                      max_escalation_levels: int}
    escalation_policy = Column(JSONB, nullable=True)

    # Current escalation depth. Incremented by the reaper when timeout_at lapses.
    escalation_level = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
