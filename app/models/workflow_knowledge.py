from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class WorkflowKnowledge(Base):
    __tablename__ = "workflow_knowledge"

    id = Column(Integer, primary_key=True)

    workflow_name = Column(String, nullable=False)

    summary = Column(Text, nullable=True)

    source_document = Column(String, nullable=True)

    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id"),
        nullable=False,
    )

    # ── Provenance link (Step 3) ──────────────────────────────────────────────
    # FK to the DocumentVersion that produced this knowledge row.
    # NULL for rows created before DocumentVersion was introduced.
    # When set, provides full provenance:
    #   WorkflowKnowledge → DocumentVersion → BRDDocument → Workspace → Tenant
    brd_document_id = Column(
        Integer,
        ForeignKey("brd_documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # FK to the specific DocumentVersion that produced this knowledge row.
    # Together with brd_document_id this gives unambiguous provenance.
    # Enforced UNIQUE by a partial index in the DB (see migration):
    #   UNIQUE (document_version_id) WHERE document_version_id IS NOT NULL
    # This prevents a retry from creating a second WorkflowKnowledge row
    # for the same version — the INSERT will raise IntegrityError instead.
    document_version_id = Column(
        Integer,
        ForeignKey("document_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
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

    # Relationships
    workspace = relationship(
        "Workspace",
        back_populates="workflows",
    )

    # Soft navigation to the source BRDDocument.
    brd_document = relationship(
        "BRDDocument",
        foreign_keys=[brd_document_id],
    )

    # Soft navigation to the specific DocumentVersion that produced this row.
    document_version = relationship(
        "DocumentVersion",
        foreign_keys=[document_version_id],
    )

    actions = relationship(
        "WorkflowActionMapping",
        back_populates="workflow",
    )

    trigger = relationship(
        "WorkflowTriggerMapping",
        back_populates="workflow",
    )
