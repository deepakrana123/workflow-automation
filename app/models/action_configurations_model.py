from sqlalchemy import Boolean, Column, DateTime, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class ActionConfiguration(Base):
    __tablename__ = "action_configurations"

    id = Column(Integer, primary_key=True)

    workflow_knowledge_id = Column(
        Integer,
        ForeignKey("workflow_knowledge.id"),
        nullable=False,
    )

    action_definition_id = Column(
        Integer,
        ForeignKey("action_definitions.id"),
        nullable=False,
    )

    workspace_integration_id = Column(
        Integer,
        ForeignKey("workspace_integrations.id"),
        nullable=True,
    )

    execution_type = Column(
        String,
        nullable=False,
        default="python",
    )

    method = Column(String)

    endpoint = Column(String)

    headers = Column(JSONB, default=dict)

    query_params = Column(JSONB, default=dict)

    body_template = Column(JSONB, default=dict)

    response_mapping = Column(JSONB, default=dict)

    timeout_seconds = Column(Integer, default=30)

    retry_policy = Column(JSONB, default=dict)

    version = Column(Integer, default=1)

    active = Column(Boolean, default=True)

    created_at = ...

    updated_at = ...
