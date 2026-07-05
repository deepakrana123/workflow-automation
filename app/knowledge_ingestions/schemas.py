from pydantic import BaseModel, Field


class TriggerExtraction(BaseModel):
    """Business event that starts a workflow."""

    name: str = Field(..., description="Name of the trigger")
    description: str = Field(
        ..., description="Brief explanation of what starts the workflow."
    )


class ActionReference(BaseModel):
    """Business action mentioned in the BRD."""

    name: str = Field(..., description="Business action name.")
    description: str = Field(..., description="What this action is expected to do.")


class BussinessRule(BaseModel):
    """Business rule extracted form the brd"""

    rule: str = Field(..., description="Business rule statement.")


class Actor(BaseModel):
    """Actor participating in the workflow."""

    name: str = Field(..., description="Actor name.")
    role: str | None = Field(
        default=None,
        description="Role or responsibilit if specified.",
    )


class ExternalSystem(BaseModel):
    """External system referenced in the document ."""

    name: str = Field(..., description="System name.")
    description: str | None = Field(
        default=None, description="Purpose of the external system.s"
    )


class WorkflowExtraction(BaseModel):
    """Strcutured information extracted from a BRD."""

    workflow_name: str = Field(..., description="Business workflow name.")
    summary: str = Field(..., description="Short summary of the workflow.")
    triggers: list[TriggerExtraction] = Field(default_factory=list)
    action_references: list[ActionReference] = Field(default_factory=list)
    business_rules: list[BussinessRule] = Field(default_factory=list)
    actors: list[Actor] = Field(default_factory=list)
    external_systems: list[ExternalSystem] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
