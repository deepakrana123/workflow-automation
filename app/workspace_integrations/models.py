from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, ForeignKey
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

    base_url = Column(String, nullable=False)

    authentication_type = Column(
        String,
        nullable=False,
    )  # api_key, bearer, oauth2, basic

    credentials = Column(
        JSONB,
        nullable=False,
        default=dict,
    )

    description = Column(Text)

    active = Column(Boolean, default=True)

    created_at = ...

    updated_at = ...
