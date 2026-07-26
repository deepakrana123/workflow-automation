from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ActionConfiguration(Base):
    __tablename__ = "action_configurations"
    __table_args__ = (
        UniqueConstraint(
            "workflow_knowledge_id",
            "action_definition_id",
            "version",
            name="uq_action_configuration_workflow_action_version",
        ),
    )

    id = Column(Integer, primary_key=True)

    # Workflow generated from BRD ingestion
    workflow_knowledge_id = Column(
        Integer,
        ForeignKey("workflow_knowledge.id"),
        nullable=False,
    )

    # Catalog action being configured
    action_definition_id = Column(
        Integer,
        ForeignKey("action_definitions.id"),
        nullable=False,
    )

    # Optional external integration (HTTP/MCP/Kafka/etc.)
    workspace_integration_id = Column(
        Integer,
        ForeignKey("workspace_integrations.id"),
        nullable=True,
    )

    # Executor discriminator
    # Supported examples: python, http, mcp, kafka, soap, ai_agent
    execution_type = Column(String, nullable=False, default="python")

    # Workflow-specific execution override.
    # Usually initialized from ActionDefinition.execution_template.
    # Examples:
    #
    # Python:
    # {"handler": "generate_pdf"}
    #
    # HTTP:
    # {
    #   "method": "POST",
    #   "endpoint": "/payments/create",
    #   "headers": {"Content-Type": "application/json"},
    #   "body_template": {"amount": "{{amount}}"},
    #   "response_mapping": {"payment_id": "$.id"},
    #   "timeout": 30,
    #   "retry_policy": {"max_retries": 3}
    # }
    configuration = Column(JSONB, nullable=False, default=dict)

    version = Column(Integer, nullable=False, default=1)

    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(  # type: ignore[arg-type]
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(  # type: ignore[arg-type]
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    action_definition = relationship("ActionDefinition")
    workflow = relationship("WorkflowKnowledge")
    workspace_integration = relationship("WorkspaceIntegration")