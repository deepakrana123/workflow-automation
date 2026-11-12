
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, ForeignKey, Integer, Text

from app.db.base import Base

EMBEDDING_DIM = 384


class WorkflowBusinessRule(Base):
    __tablename__ = "workflow_business_rule"

    id = Column(Integer, primary_key=True)

    workflow_knowledge_id = Column(
        Integer,
        ForeignKey("workflow_knowledge.id"),
        nullable=False,
    )

    rule = Column(Text, nullable=False)
    condition = Column(Text, nullable=True)
    outcome = Column(Text, nullable=True)
    responsible_role = Column(Text, nullable=True)
    threshold = Column(Text, nullable=True)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=True)
