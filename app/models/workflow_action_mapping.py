from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from sqlalchemy.sql import func
from app.db.base import Base
from sqlalchemy.orm import relationship


class WorkflowActionMapping(Base):
    __tablename__ = "workflow_action_mapping"

    id = Column(Integer, primary_key=True)

    workflow_knowledge_id = Column(
        Integer, ForeignKey("workflow_knowledge.id"), nullable=False
    )
    workflow = relationship(
        "WorkflowKnowledge",
        back_populates="actions",
    )

    extract_name = Column(String, nullable=False)
    description = Column(Text)
    matched_action_definition_id = Column(Integer, ForeignKey("action_definitions.id"))
    status = Column(String, nullable=False, default="PENDING")
    similarity_score = Column(Float, nullable=True)

    action_definition = relationship("ActionDefinition")
    

    confidence = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
