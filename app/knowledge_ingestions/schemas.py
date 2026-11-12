
from typing import Any

from pydantic import BaseModel, Field, model_validator


class TriggerExtraction(BaseModel):
    """Business event that starts or initiates a business workflow."""

    name: str = Field(..., description="Name of the business trigger.")

    description: str = Field(
        default="",
        description="Brief explanation of what starts the workflow.",
    )

    applicable_rules: list[str] = Field(
        default_factory=list,
        description=(
            "Business rules explicitly associated with this trigger. "
            "Do not infer rules that are not stated."
        ),
    )

    responsible_actors: list[str] = Field(
        default_factory=list,
        description=(
            "Actors or business roles explicitly involved in the trigger."
        ),
    )


class ActionReference(BaseModel):
    """Business action referenced in the BRD."""

    name: str = Field(
        ...,
        description="Name of the business action.",
    )

    description: str = Field(
        default="",
        description="What the business action does.",
    )

    applicable_rules: list[str] = Field(
        default_factory=list,
        description=(
            "Business rules explicitly associated with this action. "
            "Do not infer rules that are not stated."
        ),
    )

    responsible_actors: list[str] = Field(
        default_factory=list,
        description=(
            "Actors or business roles explicitly responsible for or "
            "involved in this action."
        ),
    )


class BusinessRule(BaseModel):
    """Business rule explicitly stated or clearly represented in the BRD."""

    rule: str = Field(
        ...,
        description="The business rule expressed in plain language.",
    )

    condition: str | None = Field(
        default=None,
        description=(
            "Condition under which the rule applies, if explicitly stated."
        ),
    )

    outcome: str | None = Field(
        default=None,
        description=(
            "Business outcome or decision resulting from the rule, "
            "if explicitly stated."
        ),
    )

    responsible_role: str | None = Field(
        default=None,
        description=(
            "Business role responsible for applying, approving, or "
            "enforcing the rule, if explicitly stated."
        ),
    )

    threshold: str | None = Field(
        default=None,
        description=(
            "Exact threshold, amount, percentage, score, limit, or "
            "other numeric boundary if explicitly stated."
        ),
    )


# Backward-compatible alias
BussinessRule = BusinessRule


class Actor(BaseModel):
    """Business actor participating in the workflow."""

    name: str = Field(
        ...,
        description="Actor or business role name.",
    )

    role: str | None = Field(
        default=None,
        description="Role or responsibility if explicitly specified.",
    )


class ExternalSystem(BaseModel):
    """External or named business system referenced by the BRD."""

    name: str = Field(
        ...,
        description="Name of the external or business system.",
    )

    description: str | None = Field(
        default=None,
        description="Business purpose of the system if stated.",
    )


class WorkflowExtraction(BaseModel):
    """Business knowledge extracted from a BRD."""

    workflow_name: str = Field(
        ...,
        description="Name of the business workflow.",
    )

    summary: str = Field(
        ...,
        description="Short summary based only on information in the BRD.",
    )

    triggers: list[TriggerExtraction] = Field(
        default_factory=list,
    )

    action_references: list[ActionReference] = Field(
        default_factory=list,
    )

    business_rules: list[BusinessRule] = Field(
        default_factory=list,
    )

    actors: list[Actor] = Field(
        default_factory=list,
    )

    external_systems: list[ExternalSystem] = Field(
        default_factory=list,
    )

    assumptions: list[str] = Field(
        default_factory=list,
        description=(
            "Assumptions explicitly stated in the BRD. "
            "Do not generate assumptions to fill missing information."
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def _normalise_shapes(cls, data: Any) -> Any:
        """
        Normalize common LLM output variations before validation.
        """

        if not isinstance(data, dict):
            return data

        # business_rules:
        # ["rule text"] -> [{"rule": "rule text"}]
        raw_rules = data.get("business_rules")

        if isinstance(raw_rules, list):
            normalised_rules = []
            for item in raw_rules:
                if isinstance(item, str):
                    normalised_rules.append({"rule": item})
                    continue
                if isinstance(item, dict):
                    # responsible_role:
                    # Some models emit a list of roles
                    # (e.g. ["System", "Sourcing Operations (Ops)"]) but the
                    # field is typed str | None. Coerce a list to a
                    # comma-separated string; an empty list becomes None.
                    role = item.get("responsible_role")
                    if isinstance(role, list):
                        item["responsible_role"] = (
                            ", ".join(str(r) for r in role) or None
                        )
                normalised_rules.append(item)
            data["business_rules"] = normalised_rules

        # action_references:
        # Ensure optional description exists when omitted.
        raw_actions = data.get("action_references")

        if isinstance(raw_actions, list):
            for item in raw_actions:
                if isinstance(item, dict):
                    item.setdefault("description", "")

        # triggers:
        # Ensure optional description exists when omitted.
        raw_triggers = data.get("triggers")

        if isinstance(raw_triggers, list):
            for item in raw_triggers:
                if isinstance(item, dict):
                    item.setdefault("description", "")

        # actors:
        # ["Credit Officer"] -> [{"name": "Credit Officer"}]
        raw_actors = data.get("actors")

        if isinstance(raw_actors, list):
            data["actors"] = [
                {"name": item} if isinstance(item, str) else item
                for item in raw_actors
            ]

        # responsible_actors on triggers and action_references:
        # LLMs sometimes emit [{"name": "X", "role": "Y"}] instead of ["X"].
        # Coerce dicts to a "name (role)" string; keep plain strings as-is.
        def _coerce_responsible_actors(items: list) -> list:
            result = []
            for item in items:
                if isinstance(item, dict):
                    name = item.get("name") or ""
                    role = item.get("role") or ""
                    result.append(f"{name} ({role})".strip(" ()") if role else name)
                elif isinstance(item, str):
                    result.append(item)
            return result

        for collection_key in ("triggers", "action_references"):
            raw_collection = data.get(collection_key)
            if isinstance(raw_collection, list):
                for item in raw_collection:
                    if isinstance(item, dict):
                        raw_ra = item.get("responsible_actors")
                        if isinstance(raw_ra, list):
                            item["responsible_actors"] = _coerce_responsible_actors(raw_ra)

        return data