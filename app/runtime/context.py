"""
app/runtime/context.py

RetrievalContext and RuntimeContext — structured context objects passed through
the integrated runtime pipeline.

Design principles:
  - Context is resolved server-side from authentication headers; never trust client claims.
  - All fields are optional except user_id + workspace_id — global search and
    workflow-less lookups are valid use cases.
  - allowed_action_ids=None means "derive from RBAC at retrieval time".
    allowed_action_ids=set() means "nothing is allowed" (explicit empty).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RetrievalContext:
    """
    Scopes a retrieval query to the intersection of RBAC-allowed and
    workflow-available actions.

    Required:
        user_id       — caller identity (from X-User-Id header or future JWT)
        workspace_id  — workspace boundary

    Optional workflow scope (when inside an active workflow execution):
        workflow_id           — the workflow definition being executed
        workflow_execution_id — the specific execution run
        current_step_id       — the step the execution is currently on

    Optional pre-resolved sets (populated by RBAC resolver before retrieval):
        allowed_action_ids  — set of ActionDefinition.id the user may access;
                               None → not yet resolved (pipeline will resolve)
        allowed_trigger_ids — same for triggers

    metadata_filters — arbitrary key/value pairs for future extension
    """

    user_id: str
    workspace_id: int

    workflow_id: Optional[int] = None
    workflow_execution_id: Optional[int] = None
    current_step_id: Optional[str] = None

    # Resolved by RBACCapabilityResolver before retrieval
    allowed_action_ids: Optional[set[int]] = None
    allowed_trigger_ids: Optional[set[int]] = None

    # User's roles in this workspace (resolved once, reused)
    roles: list[str] = field(default_factory=list)

    metadata_filters: dict = field(default_factory=dict)

    def has_workflow_scope(self) -> bool:
        return self.workflow_id is not None

    def has_step_scope(self) -> bool:
        return self.current_step_id is not None


@dataclass
class RuleEvaluationContext:
    """
    Carries all facts needed for deterministic rule evaluation.

    request_data         — user-provided request body (sanitised)
    previous_step_outputs— accumulated WorkflowContext.outputs up to this step
    """

    user_id: str
    workspace_id: int
    workflow_id: Optional[int] = None
    workflow_execution_id: Optional[int] = None
    step_id: Optional[str] = None
    action_id: Optional[int] = None
    actor_roles: list[str] = field(default_factory=list)
    request_data: dict = field(default_factory=dict)
    previous_step_outputs: dict = field(default_factory=dict)


@dataclass
class RuleEvaluationResult:
    """
    Structured result from the rule engine layer.

    Never return a plain bool — callers need to know WHY a rule failed.
    """

    allowed: bool
    decisions: list[dict] = field(default_factory=list)
    failed_rules: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "allowed":      self.allowed,
            "decisions":    self.decisions,
            "failed_rules": self.failed_rules,
            "warnings":     self.warnings,
        }
