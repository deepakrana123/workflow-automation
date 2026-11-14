from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreate(BaseModel):
    tenant_id: int = Field(..., description="ID of the tenant (bank) that owns this workspace.")
    name: str = Field(..., description="Machine-readable name, unique within the tenant.")
    display_name: str = Field(..., description="Human-friendly label shown in the UI.")
    description: str | None = None


class WorkspaceResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    display_name: str
    description: str | None = None
    active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
