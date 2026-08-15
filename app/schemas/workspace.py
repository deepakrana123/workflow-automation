from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(..., description="Unique machine name (slug).")
    display_name: str = Field(..., description="Human-friendly name.")
    description: str | None = None
    organization_name: str | None = None


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: str | None = None
    organization_name: str | None = None
    active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
