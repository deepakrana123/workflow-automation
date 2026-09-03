from pydantic import BaseModel, Field


class TriggerExtraction(BaseModel):
    """Business event that starts a workflow."""

    name: str = Field(..., description="Name of the trigger.")
    description: str = Field(..., description="Brief explanation of what starts the workflow.")

    # Rules from the BRD that specifically apply to this trigger.
    # Only include rules that are explicitly tied to this trigger event.
    applicable_rules: list[str] = Field(
        default_factory=list,
        description=(
            "Business rules from the document that specifically apply to this trigger. "
            "Only include rules explicitly tied to this trigger event. "
            "Leave empty if no rules are directly associated."
        ),
    )

    # Actors responsible for or involved in this trigger event.
    responsible_actors: list[str] = Field(
        default_factory=list,
        description=(
            "Actor names (and roles if stated) responsible for or involved in this trigger. "
            "Format: 'Name (role)' if role is present, else just 'Name'. "
            "Leave empty if no actors are directly associated."
        ),
    )


class ActionReference(BaseModel):
    """Business action referenced in the BRD."""

    name: str = Field(..., description="Business action name.")
    description: str = Field(..., description="What this action is expected to do.")

    # Rules from the BRD that specifically apply to this action.
    # Only include rules that are explicitly tied to this action — not all workspace rules.
    applicable_rules: list[str] = Field(
        default_factory=list,
        description=(
            "Business rules from the document that specifically apply to this action. "
            "For example: 'Manual approval required above ₹5L' belongs to the approval action, "
            "not to every action. Only include rules explicitly tied to this action. "
            "Leave empty if no rules are directly associated."
        ),
    )

    # Actors responsible for executing or approving this action.
    responsible_actors: list[str] = Field(
        default_factory=list,
        description=(
            "Actor names (and roles if stated) responsible for or involved in this action. "
            "Format: 'Name (role)' if role is present, else just 'Name'. "
            "Leave empty if no actors are directly associated."
        ),
    )


class BusinessRule(BaseModel):
    """Business rule extracted from the BRD."""

    rule: str = Field(..., description="Business rule statement.")


# Backward-compatible alias — remove once all callers use BusinessRule
BussinessRule = BusinessRule


class Actor(BaseModel):
    """Actor participating in the workflow."""

    name: str = Field(..., description="Actor name.")
    role: str | None = Field(default=None, description="Role or responsibility if specified.")


class ExternalSystem(BaseModel):
    """External system referenced in the document."""

    name: str = Field(..., description="System name.")
    description: str | None = Field(default=None, description="Purpose of the external system.")


class WorkflowExtraction(BaseModel):
    """Structured information extracted from a BRD."""

    workflow_name: str = Field(..., description="Business workflow name.")
    summary: str = Field(..., description="Short summary of the workflow.")
    triggers: list[TriggerExtraction] = Field(default_factory=list)
    action_references: list[ActionReference] = Field(default_factory=list)
    business_rules: list[BusinessRule] = Field(default_factory=list)
    actors: list[Actor] = Field(default_factory=list)
    external_systems: list[ExternalSystem] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
