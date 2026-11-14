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
    # No back_populates on BRDDocument — the reverse list is on
    # IngestionAttempt.extracted_knowledge, not here.
    brd_document = relationship(
        "BRDDocument",
        foreign_keys=[brd_document_id],
    )

    actions = relationship(
        "WorkflowActionMapping",
        back_populates="workflow",
    )

    trigger = relationship(
        "WorkflowTriggerMapping",
        back_populates="workflow",
    )
