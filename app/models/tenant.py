from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Tenant(Base):
    """
    A bank (or other financial institution) that uses the platform.

    One Tenant → many Workspaces (each workspace is a product/knowledge domain,
    e.g. "Personal Loan" inside HDFC Bank).

    Tenant is the outermost isolation boundary.  Every workspace, BRD, workflow,
    rule, and role-assignment is owned — directly or transitively — by a tenant.
    """

    __tablename__ = "tenants"

    # Surrogate primary key.  Used as the FK target by workspaces.tenant_id.
    id = Column(Integer, primary_key=True)

    # Short machine-readable identifier, unique across the platform.
    # Used in API paths and log messages.  Immutable after creation.
    # Example: "hdfc_bank", "axis_bank"
    name = Column(String, nullable=False, unique=True, index=True)

    # URL-safe slug, unique across the platform.
    # Distinct from `name` so the display name can change without affecting URLs.
    # Example: "hdfc-bank", "axis-bank"
    slug = Column(String, nullable=False, unique=True, index=True)

    # Human-readable label shown in the UI.
    # Example: "HDFC Bank", "Axis Bank"
    display_name = Column(String, nullable=False)

    # Soft-delete flag.  Inactive tenants are hidden from normal queries but
    # their data is retained for audit purposes.
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

    # All product/knowledge-domain workspaces that belong to this tenant.
    # back_populates matches Workspace.tenant.
    workspaces = relationship(
        "Workspace",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
