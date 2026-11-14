from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TenantCreate(BaseModel):
    name: str = Field(
        ...,
        description="Machine-readable identifier, unique across the platform. "
                    "Example: 'hdfc_bank'",
    )
    slug: str = Field(
        ...,
        description="URL-safe slug, unique across the platform. "
                    "Example: 'hdfc-bank'",
    )
    display_name: str = Field(
        ...,
        description="Human-readable label shown in the UI. Example: 'HDFC Bank'",
    )


class TenantResponse(BaseModel):
    id: int
    name: str
    slug: str
    display_name: str
    active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
