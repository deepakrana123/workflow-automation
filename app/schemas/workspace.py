from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.workspace import WORKSPACE_LEVELS, _PARENT_LEVEL

# Valid level literals
WorkspaceLevel = Literal["global", "region", "zone", "branch"]


class WorkspaceCreate(BaseModel):
    name: str = Field(..., description="Unique machine name (slug).")
    display_name: str = Field(..., description="Human-friendly name.")
    description: str | None = None
    organization_name: str | None = None
    # Hierarchy fields — default branch so existing callers are unaffected
    level: WorkspaceLevel = "branch"
    parent_id: int | None = None

    @model_validator(mode="after")
    def validate_hierarchy(self) -> "WorkspaceCreate":
        """
        Hierarchy validation is relaxed for now — all workspaces default to
        'branch' level and parent_id is optional. When multi-level rule
        inheritance is needed in the future, this validator can be tightened.
        """
        return self


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: str | None = None
    organization_name: str | None = None
    active: bool
    level: str = "branch"
    parent_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
