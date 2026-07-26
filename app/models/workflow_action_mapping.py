import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class MappingStatus(str, enum.Enum):
    PENDING   = "PENDING"
    MAPPED    = "MAPPED"
    UNMAPPED  = "UNMAPPED"
    FAILED    = "FAILED"


class WorkflowActionMapping(Base):
    __tablename__ = "workflow_action_mapping"

    id = Column(Integer, primary_key=True)

    workflow_knowledge_id = Column(
        Integer,
        ForeignKey("workflow_knowledge.id"),
        nullable=False,
    )

    extract_name = Column(String, nullable=False)

    description = Column(Text)

    matched_action_definition_id = Column(
        Integer,
        ForeignKey("action_definitions.id"),
        nullable=True,
    )

    status = Column(
        Enum(MappingStatus, name="mappingstatus"),
        nullable=False,
        default=MappingStatus.PENDING,
    )

    similarity_score = Column(Float, nullable=True)

    confidence = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workflow = relationship(
        "WorkflowKnowledge",
        back_populates="actions",
    )

    action_definition = relationship("ActionDefinition")
