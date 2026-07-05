from sqlalchemy import Column, ForeignKey, Integer, Text
from app.db.base import Base


class WorkflowBusinessRule(Base):
    __tablename__ = "workflow_business_rule"
    id = Column(Integer, primary_key=True)
    
    workflow_knowledge_id=Column(
        Integer,ForeignKey("workflow_knowledge.id"),
        nullable=False
    )
    
    rule=Column(Text,nullable=False)
