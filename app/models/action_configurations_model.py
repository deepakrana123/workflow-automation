from sqlalchemy import Boolean, Column, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class ActionConfiguration(Base):
    __tablename__ = "action_configurations"

    id = Column(Integer, primary_key=True)

    action_definition_id = Column(
        Integer,
        ForeignKey("action_definitions.id"),
        nullable=False,
    )

    workflow_knowledge_id = Column(
        Integer,
        ForeignKey("workflow_knowledge.id"),
        nullable=True,
    )

    version = Column(Integer, nullable=False, default=1)

    # Execution metadata for this action in this workflow context.
    # Minimum required: {"execution_type": "python", "handler": "<function_name>"}
    # Future execution_types: http, mcp, ai_agent, human_task
    configuration = Column(JSONB, nullable=False, default=dict)

    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    action_definition = relationship("ActionDefinition")
    workflow = relationship("WorkflowKnowledge")
