"""
app/workflow_execution/schemas/action_result.py

Standardized contract for every executable action in the system.

Every action — Python handlers, REST integrations, MCP tools, AI agents —
must return ActionResult. The execution engine consumes only ActionResult.

Usage:
    from app.workflow_execution.schemas.action_result import ActionResult

    # Minimal success
    return ActionResult(success=True)

    # Success with outputs
    return ActionResult(
        success=True,
        outputs={"credit_score": 720, "risk": "LOW"},
        message="CIBIL check completed",
    )

    # Failure
    return ActionResult(
        success=False,
        error="Bureau API timeout",
        message="CIBIL check failed after 3 retries",
    )
"""

from typing import Any
from pydantic import BaseModel, Field


class ActionResult(BaseModel):
    """
    Standardized result contract for every executable action.

    success  — True if the action completed successfully. Retry logic reads only this.
    outputs  — Key-value data produced by the action. Merged into WorkflowContext.
    message  — Human-readable summary of what happened.
    error    — Error description when success=False.
    metadata — Internal diagnostics (provider, latency, reference IDs). Not for business logic.
    """

    success: bool
    outputs: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
