from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.sql import func

from app.db.base import Base
from sqlalchemy.orm import relationship


# Valid workspace levels — ordered from broadest to narrowest.
WORKSPACE_LEVELS = ("global", "region", "zone", "branch")

# Maps each level to its immediate parent level.
_PARENT_LEVEL = {
    "region": "global",
    "zone": "region",
    "branch": "zone",
}


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False, unique=True)

    display_name = Column(String, nullable=False)

    description = Column(String, nullable=True)

    organization_name = Column(String, nullable=True)

    active = Column(Boolean, nullable=False, default=True)

    # ── Hierarchy fields (added by migration c1d2e3f4a5b6) ───────────────────
    # One of: global, region, zone, branch.
    # Existing rows were backfilled to 'branch'.
    level = Column(String(20), nullable=False, default="branch")

    # Self-referential FK — NULL only for level='global'.
    parent_id = Column(
        Integer,
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    workflows = relationship(
        "WorkflowKnowledge",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )

    # Self-referential: parent (many-to-one) and children (one-to-many)
    # remote_side=[id] tells SQLAlchemy that `id` is on the "one" side.
    parent = relationship(
        "Workspace",
        foreign_keys=[parent_id],
        remote_side="Workspace.id",
        back_populates="children",
    )
    children = relationship(
        "Workspace",
        foreign_keys=[parent_id],
        back_populates="parent",
    )