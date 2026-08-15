"""
Pydantic schemas for WorkspaceIntegration request / response.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Allowed enum values ───────────────────────────────────────────────────────

VALID_PROVIDER_TYPES    = {"http", "soap", "grpc", "kafka", "mcp"}
VALID_AUTH_TYPES        = {"api_key", "bearer", "oauth2", "basic", "none"}

# Required credential keys per auth type
_AUTH_REQUIRED_KEYS: dict[str, set[str]] = {
    "api_key": {"key"},
    "bearer":  {"token"},
    "basic":   {"username", "password"},
    "oauth2":  {"access_token"},
    "none":    set(),
}


# ── Request schemas ───────────────────────────────────────────────────────────

class WorkspaceIntegrationCreate(BaseModel):
    name:                str   = Field(..., min_length=1, max_length=255)
    provider_type:       str   = Field(...)
    base_url:            str   = Field(..., min_length=1)
    authentication_type: str   = Field(...)
    credentials:         dict[str, Any] = Field(default_factory=dict)
    description:         str | None = None

    @field_validator("provider_type")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        if v not in VALID_PROVIDER_TYPES:
            raise ValueError(
                f"Invalid provider_type '{v}'. Allowed: {sorted(VALID_PROVIDER_TYPES)}"
            )
        return v

    @field_validator("authentication_type")
    @classmethod
    def validate_auth_type(cls, v: str) -> str:
        if v not in VALID_AUTH_TYPES:
            raise ValueError(
                f"Invalid authentication_type '{v}'. Allowed: {sorted(VALID_AUTH_TYPES)}"
            )
        return v

    @model_validator(mode="after")
    def validate_credentials(self) -> WorkspaceIntegrationCreate:
        required = _AUTH_REQUIRED_KEYS.get(self.authentication_type, set())
        missing  = required - set(self.credentials.keys())
        if missing:
            raise ValueError(
                f"credentials missing required keys for "
                f"authentication_type='{self.authentication_type}': {sorted(missing)}"
            )
        return self


class WorkspaceIntegrationUpdate(BaseModel):
    name:                str | None   = Field(default=None, min_length=1, max_length=255)
    provider_type:       str | None   = None
    base_url:            str | None   = Field(default=None, min_length=1)
    authentication_type: str | None   = None
    credentials:         dict[str, Any] | None = None
    description:         str | None   = None

    @field_validator("provider_type")
    @classmethod
    def validate_provider(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_PROVIDER_TYPES:
            raise ValueError(
                f"Invalid provider_type '{v}'. Allowed: {sorted(VALID_PROVIDER_TYPES)}"
            )
        return v

    @field_validator("authentication_type")
    @classmethod
    def validate_auth_type(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_AUTH_TYPES:
            raise ValueError(
                f"Invalid authentication_type '{v}'. Allowed: {sorted(VALID_AUTH_TYPES)}"
            )
        return v


# ── Response schemas ──────────────────────────────────────────────────────────

class WorkspaceIntegrationResponse(BaseModel):
    id:                  int
    workspace_id:        int
    name:                str
    provider_type:       str
    base_url:            str
    authentication_type: str
    description:         str | None
    active:              bool
    created_at:          datetime
    updated_at:          datetime

    model_config = {"from_attributes": True}
