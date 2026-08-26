from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True, nullable=True)
    action = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)

    request_payload = Column(Text, nullable=True)
    response_payload = Column(Text, nullable=True)

    # ── Extended fields (migration c1d2e3f4a5b6) ──────────────────────────────
    # Who triggered this event (user_id from the caller's session/token)
    user_id = Column(String(255), nullable=True, index=True)
    # Which workspace the event belongs to
    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Valid event_type values ───────────────────────────────────────────────────
# Pre-existing event types are whatever callers already use.
# New event types added by this feature:
AUDIT_EVENT_RBAC_ASSIGNMENT          = "rbac_assignment"
AUDIT_EVENT_PERMISSION_CHECK         = "permission_check"
AUDIT_EVENT_PERMISSION_DENIED        = "permission_denied"
AUDIT_EVENT_RULE_CREATED             = "rule_created"
AUDIT_EVENT_RULE_CONFLICT            = "rule_conflict"
AUDIT_EVENT_STEP_RULE_BLOCKED        = "execution_step_rule_blocked"
AUDIT_EVENT_WORKFLOW_PUBLISHED       = "workflow_published"
AUDIT_EVENT_SKILL_FILE_GENERATED     = "skill_file_generated"
AUDIT_EVENT_HUMANTASK_ESCALATED      = "humantask_escalated"
