from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func
from app.db.base import Base
from sqlalchemy.orm import relationship

class WorkflowKnowledge(Base):
    __tablename__ = "workflow_knowledge"
    id = Column(Integer, primary_key=True)

    workflow_name = Column(String, nullable=False)

    summary = Column(Text, nullable=True)

    source_document = Column(String, nullable=True)
    
    actions = relationship(
        "WorkflowActionMapping",
        back_populates="workflow",
    )
    
    trigger = relationship(
        "WorkflowTriggerMapping",
        back_populates="workflow",
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
