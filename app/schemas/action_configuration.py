"""
Pydantic schemas for ActionConfiguration request / response.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


VALID_EXECUTION_TYPES = {"python", "http", "mcp", "kafka", "soap", "ai_agent"}


# ── Request schemas ───────────────────────────────────────────────────────────

class ActionConfigurationUpdate(BaseModel):
    """
    Full update — replaces execution_type, workspace_integration_id,
    and the entire configuration blob.
    Creates a new version; deactivates the previous active version.
    """
    execution_type:           str              = Field(...)
    workspace_integration_id: int | None       = None
    configuration:            dict[str, Any]   = Field(default_factory=dict)

    @field_validator("execution_type")
    @classmethod
    def validate_execution_type(cls, v: str) -> str:
        if v not in VALID_EXECUTION_TYPES:
            raise ValueError(
                f"Invalid execution_type '{v}'. Allowed: {sorted(VALID_EXECUTION_TYPES)}"
            )
        return v

    @field_validator("configuration")
    @classmethod
    def validate_configuration(cls, v: dict) -> dict:
        # Validated per execution_type in the service layer where
        # workspace_integration is also available.
        return v


# ── Response schemas ──────────────────────────────────────────────────────────

class ActionConfigurationResponse(BaseModel):
    id:                       int
    workflow_knowledge_id:    int
    action_definition_id:     int
    workspace_integration_id: int | None
    execution_type:           str
    configuration:            dict[str, Any]
    version:                  int
    active:                   bool
    created_at:               datetime
    updated_at:               datetime

    model_config = {"from_attributes": True}
