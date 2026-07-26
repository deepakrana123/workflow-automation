from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    ForeignKey
)
from sqlalchemy.sql import func

from app.db.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

class WorkspaceIntegration(Base):
    __tablename__ = "workspace_integrations"

    id = Column(Integer, primary_key=True)

    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id"),
        nullable=False,
    )

    name = Column(String, nullable=False)

    provider = Column(String, nullable=False)

    integration_type = Column(
        String,
        nullable=False,
    )  # http, soap, grpc, kafka, mcp

    base_url = Column(String, nullable=True)

    authentication = Column(JSONB, nullable=False, default=dict)

    credentials = Column(JSONB, nullable=False, default=dict)

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