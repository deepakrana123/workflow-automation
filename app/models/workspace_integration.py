from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base


class WorkspaceIntegration(Base):
    __tablename__ = "workspace_integrations"

    id = Column(Integer, primary_key=True)

    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id"),
        nullable=False,
    )

    name = Column(String, nullable=False)

    provider_type = Column(
        String,
        nullable=False,
    )  # http, soap, grpc, kafka, mcp

    base_url = Column(String, nullable=True)

    authentication_type = Column(
        String,
        nullable=False,
    )  # api_key, bearer, oauth2, basic

    credentials = Column(JSONB, nullable=False, default=dict)

    description = Column(Text, nullable=True)

    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )