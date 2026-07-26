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

    actions = relationship(
        "WorkflowActionMapping",
        back_populates="workflow",
    )

    trigger = relationship(
        "WorkflowTriggerMapping",
        back_populates="workflow",
    )
