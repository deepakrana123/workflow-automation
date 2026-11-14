from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Workspace(Base):
    """
    A product / knowledge domain belonging to a Tenant (bank).

    Examples:
      - HDFC Bank  → Personal Loan
      - Axis Bank  → Personal Loan   (same name, different tenant — allowed)

    Every BRD, workflow, extracted knowledge, business rule, role-assignment
    and integration is owned by a Workspace, which is in turn owned by a
    Tenant.  This is the second level of the isolation hierarchy:

        Tenant (bank)  →  Workspace (product domain)  →  all domain data
    """

    __tablename__ = "workspaces"

    __table_args__ = (
        # Two workspaces inside the same tenant cannot share a name.
        # Different tenants can have workspaces with the same name (e.g. both
        # have "Personal Loan").
        UniqueConstraint("tenant_id", "name", name="uq_workspace_tenant_name"),
    )

    # ── Primary key ───────────────────────────────────────────────────────────
    id = Column(Integer, primary_key=True)

    # ── Tenant ownership (non-nullable — every workspace belongs to a bank) ──
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    # Machine-readable name, unique within a tenant.
    # Example: "personal_loan"
    name = Column(String, nullable=False)

    # Human-readable label shown in the UI.
    # Example: "Personal Loan"
    display_name = Column(String, nullable=False)

    # Optional free-text description of the workspace's purpose.
    description = Column(String, nullable=True)

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    # Parent tenant (many workspaces → one tenant).
    tenant = relationship(
        "Tenant",
        back_populates="workspaces",
    )

    # BRD knowledge documents ingested into this workspace.
    # back_populates matches WorkflowKnowledge.workspace.
    workflows = relationship(
        "WorkflowKnowledge",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
