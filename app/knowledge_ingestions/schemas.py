from pydantic import BaseModel, Field, model_validator
from typing import Any


class TriggerExtraction(BaseModel):
    """Business event that starts a workflow."""

    name: str = Field(..., description="Name of the trigger.")
    description: str = Field(default="", description="Brief explanation of what starts the workflow.")

    applicable_rules: list[str] = Field(
        default_factory=list,
        description=(
            "Business rules from the document that specifically apply to this trigger. "
            "Only include rules explicitly tied to this trigger event. "
            "Leave empty if no rules are directly associated."
        ),
    )

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
    description: str = Field(default="", description="What this action is expected to do.")

    applicable_rules: list[str] = Field(
        default_factory=list,
        description=(
            "Business rules from the document that specifically apply to this action. "
            "Leave empty if no rules are directly associated."
        ),
    )

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


# Backward-compatible alias
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

    @model_validator(mode="before")
    @classmethod
    def _normalise_shapes(cls, data: Any) -> Any:
        """
        Coerce LLM output variations into the expected shapes before
        field-level validation runs. Models sometimes return:

          business_rules: ["rule text", ...]            → wrap as {"rule": "..."}
          business_rules: [{"rule": "..."}, ...]        → pass through unchanged

          action_references: [{"name": "..."}, ...]     → add description="" if missing
          triggers:          [{"name": "..."}, ...]     → add description="" if missing

          actors: ["Actor Name", ...]                   → wrap as {"name": "..."}
          actors: [{"name": "..."}, ...]                → pass through unchanged
        """
        if not isinstance(data, dict):
            return data

        # ── business_rules: plain strings → {"rule": str} ────────────────────
        raw_rules = data.get("business_rules")
        if isinstance(raw_rules, list):
            coerced = []
            for item in raw_rules:
                if isinstance(item, str):
                    coerced.append({"rule": item})
                else:
                    coerced.append(item)
            data["business_rules"] = coerced

        # ── action_references: ensure description exists ───────────────────────
        raw_actions = data.get("action_references")
        if isinstance(raw_actions, list):
            for item in raw_actions:
                if isinstance(item, dict) and "description" not in item:
                    item["description"] = ""

        # ── triggers: ensure description exists ──────────────────────────────
        raw_triggers = data.get("triggers")
        if isinstance(raw_triggers, list):
            for item in raw_triggers:
                if isinstance(item, dict) and "description" not in item:
                    item["description"] = ""

        # ── actors: plain strings → {"name": str} ────────────────────────────
        raw_actors = data.get("actors")
        if isinstance(raw_actors, list):
            coerced = []
            for item in raw_actors:
                if isinstance(item, str):
                    coerced.append({"name": item})
                else:
                    coerced.append(item)
            data["actors"] = coerced

        return data
