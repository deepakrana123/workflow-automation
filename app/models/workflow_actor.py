from sqlalchemy import (Column,ForeignKey,Integer,String)

from app.db.base import Base



class WorkflowActor(Base):
    __tablename__="workflow_actors"
    
    id = Column(Integer,primary_key=True)
    
    workflow_knowledge_id=Column(
        Integer,ForeignKey("workflow_knowledge.id"),
        nullable=False
    )
    name = Column(String, nullable=False)

    role = Column(String)