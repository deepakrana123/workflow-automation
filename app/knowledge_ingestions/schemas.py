# from pydantic import BaseModel, Field, model_validator
# from typing import Any


# class TriggerExtraction(BaseModel):
#     """Business event that starts a workflow."""

#     name: str = Field(..., description="Name of the trigger.")
#     description: str = Field(default="", description="Brief explanation of what starts the workflow.")

#     applicable_rules: list[str] = Field(
#         default_factory=list,
#         description=(
#             "Business rules from the document that specifically apply to this trigger. "
#             "Only include rules explicitly tied to this trigger event. "
#             "Leave empty if no rules are directly associated."
#         ),
#     )

#     responsible_actors: list[str] = Field(
#         default_factory=list,
#         description=(
#             "Actor names (and roles if stated) responsible for or involved in this trigger. "
#             "Format: 'Name (role)' if role is present, else just 'Name'. "
#             "Leave empty if no actors are directly associated."
#         ),
#     )


# class ActionReference(BaseModel):
#     """Business action referenced in the BRD."""

#     name: str = Field(..., description="Business action name.")
#     description: str = Field(default="", description="What this action is expected to do.")

#     applicable_rules: list[str] = Field(
#         default_factory=list,
#         description=(
#             "Business rules from the document that specifically apply to this action. "
#             "Leave empty if no rules are directly associated."
#         ),
#     )

#     responsible_actors: list[str] = Field(
#         default_factory=list,
#         description=(
#             "Actor names (and roles if stated) responsible for or involved in this action. "
#             "Format: 'Name (role)' if role is present, else just 'Name'. "
#             "Leave empty if no actors are directly associated."
#         ),
#     )


# class BusinessRule(BaseModel):
#     """Business rule extracted from the BRD."""

#     rule: str = Field(..., description="Business rule statement.")


# # Backward-compatible alias
# BussinessRule = BusinessRule


# class Actor(BaseModel):
#     """Actor participating in the workflow."""

#     name: str = Field(..., description="Actor name.")
#     role: str | None = Field(default=None, description="Role or responsibility if specified.")


# class ExternalSystem(BaseModel):
#     """External system referenced in the document."""

#     name: str = Field(..., description="System name.")
#     description: str | None = Field(default=None, description="Purpose of the external system.")


# class WorkflowExtraction(BaseModel):
#     """Structured information extracted from a BRD."""

#     workflow_name: str = Field(..., description="Business workflow name.")
#     summary: str = Field(..., description="Short summary of the workflow.")
#     triggers: list[TriggerExtraction] = Field(default_factory=list)
#     action_references: list[ActionReference] = Field(default_factory=list)
#     business_rules: list[BusinessRule] = Field(default_factory=list)
#     actors: list[Actor] = Field(default_factory=list)
#     external_systems: list[ExternalSystem] = Field(default_factory=list)
#     assumptions: list[str] = Field(default_factory=list)

#     @model_validator(mode="before")
#     @classmethod
#     def _normalise_shapes(cls, data: Any) -> Any:
#         """
#         Coerce LLM output variations into the expected shapes before
#         field-level validation runs. Models sometimes return:

#           business_rules: ["rule text", ...]            → wrap as {"rule": "..."}
#           business_rules: [{"rule": "..."}, ...]        → pass through unchanged

#           action_references: [{"name": "..."}, ...]     → add description="" if missing
#           triggers:          [{"name": "..."}, ...]     → add description="" if missing

#           actors: ["Actor Name", ...]                   → wrap as {"name": "..."}
#           actors: [{"name": "..."}, ...]                → pass through unchanged
#         """
#         if not isinstance(data, dict):
#             return data

#         # ── business_rules: plain strings → {"rule": str} ────────────────────
#         raw_rules = data.get("business_rules")
#         if isinstance(raw_rules, list):
#             coerced = []
#             for item in raw_rules:
#                 if isinstance(item, str):
#                     coerced.append({"rule": item})
#                 else:
#                     coerced.append(item)
#             data["business_rules"] = coerced

#         # ── action_references: ensure description exists ───────────────────────
#         raw_actions = data.get("action_references")
#         if isinstance(raw_actions, list):
#             for item in raw_actions:
#                 if isinstance(item, dict) and "description" not in item:
#                     item["description"] = ""

#         # ── triggers: ensure description exists ──────────────────────────────
#         raw_triggers = data.get("triggers")
#         if isinstance(raw_triggers, list):
#             for item in raw_triggers:
#                 if isinstance(item, dict) and "description" not in item:
#                     item["description"] = ""

#         # ── actors: plain strings → {"name": str} ────────────────────────────
#         raw_actors = data.get("actors")
#         if isinstance(raw_actors, list):
#             coerced = []
#             for item in raw_actors:
#                 if isinstance(item, str):
#                     coerced.append({"name": item})
#                 else:
#                     coerced.append(item)
#             data["actors"] = coerced

#         return data


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
            data["business_rules"] = [
                {"rule": item} if isinstance(item, str) else item
                for item in raw_rules
            ]

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

        return data