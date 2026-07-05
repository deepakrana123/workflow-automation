from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app.db.base import Base


class WorkflowExternalSystem(Base):
    __tablename__ = "workflow_external_systems"

    id = Column(Integer, primary_key=True)

    workflow_knowledge_id = Column(
        Integer,
        ForeignKey("workflow_knowledge.id", ondelete="CASCADE"),
        nullable=False,
    )

    name = Column(String, nullable=False)

    description = Column(Text)
