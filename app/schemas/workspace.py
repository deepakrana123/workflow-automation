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
        """Enforce parent_id requirements based on level."""
        if self.level == "global":
            if self.parent_id is not None:
                raise ValueError("A global workspace must not have a parent_id.")
        else:
            if self.parent_id is None:
                raise ValueError(
                    f"A '{self.level}' workspace requires a parent_id. "
                    f"Expected parent level: '{_PARENT_LEVEL[self.level]}'."
                )
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
