"""
app/capabilities/service.py

CapabilityService — builds CapabilityView projections for actions and
applies RBAC filtering so callers only see what they are permitted to use.

This service sits BETWEEN retrieval and execution:

  RetrievalPipeline.search_actions(query, embedding)
       ↓  RankedCandidate[]
  CapabilityService.filter_by_permission(candidates, user_id, workspace_id)
       ↓  list[CapabilityView]  (only permitted ones)
  WorkflowDispatchService.dispatch(...)

It does NOT modify the retrieval pipeline. The retrieval system remains
independent and unaware of permissions.

Usage:
    svc = CapabilityService(db)
    capabilities = svc.get_for_user(user_id, workspace_id)
    capability   = svc.get_by_action_name("approve_loan", workspace_id)
    filtered     = svc.filter_by_permission(ranked_candidates, user_id, workspace_id)
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.action_definitions import ActionDefinition
from app.models.business_rule_definition import BusinessRuleDefinition
from app.models.workflow import Workflow
from app.models.workflow_business_rule import WorkflowBusinessRule
from app.models.role_assignment import get_permissions_for_role
from app.rbac.permission_checker import PermissionChecker
from app.rbac.rule_inheritance import resolve_effective_rules
from app.capabilities.model import CapabilityView
from app.core.logger import logger


class CapabilityService:

    def __init__(self, db: Session):
        self._db = db
        self._checker = PermissionChecker(db)

    # ── Public interface ──────────────────────────────────────────────────────

    def get_for_user(
        self,
        user_id: str,
        workspace_id: int,
    ) -> list[CapabilityView]:
        """Return all capabilities the user can read in this workspace."""
        # Permission check once — not per action
        if not self._checker.can(user_id, "capability:read", workspace_id):
            return []

        all_actions = (
            self._db.query(ActionDefinition)
            .filter(ActionDefinition.active.is_(True))
            .all()
        )

        # Resolve effective rules once for the workspace — not per action (N+1 fix)
        effective_rules = resolve_effective_rules(workspace_id, self._db, field=None)

        return [self._build_view_with_rules(a, workspace_id, effective_rules) for a in all_actions]

    def get_by_action_name(
        self,
        action_name: str,
        workspace_id: int,
    ) -> CapabilityView | None:
        """Build a CapabilityView for a single action in the given workspace."""
        action = (
            self._db.query(ActionDefinition)
            .filter(
                ActionDefinition.name == action_name,
                ActionDefinition.active.is_(True),
            )
            .first()
        )
        if action is None:
            return None
        return self._build_view(action, workspace_id)

    def filter_by_permission(
        self,
        candidates: list,           # list[RankedCandidate] from retrieval
        user_id: str,
        workspace_id: int,
    ) -> list[CapabilityView]:
        """Filter retrieval candidates to those the user is permitted to access.

        The retrieval system returns RankedCandidate objects whose .entity is
        an ActionDefinition. This method wraps each into a CapabilityView
        and drops those the user cannot access.

        Retrieval ranking is preserved; only unauthorized entries are removed.
        """
        if not self._checker.can(user_id, "capability:read", workspace_id):
            return []

        # Resolve rules once for the whole batch — not per candidate
        effective_rules = resolve_effective_rules(workspace_id, self._db, field=None)

        result = []
        for candidate in candidates:
            action = getattr(candidate, "entity", None)
            if action is None or not isinstance(action, ActionDefinition):
                continue
            result.append(self._build_view_with_rules(action, workspace_id, effective_rules))
        return result

    def get_linked_workflows(
        self,
        action_name: str,
        workspace_id: int,
    ) -> list[int]:
        """Return IDs of published workflows in this workspace that contain action_name."""
        workflows = (
            self._db.query(Workflow)
            .filter(
                Workflow.workspace_id == workspace_id,
                Workflow.status == "published",
                Workflow.parsed_rule_json.isnot(None),
            )
            .all()
        )
        linked = []
        for wf in workflows:
            steps = (wf.parsed_rule_json or {}).get("steps", [])
            if any(s.get("action") == action_name for s in steps):
                linked.append(wf.id)
        return linked

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_view(self, action: ActionDefinition, workspace_id: int) -> CapabilityView:
        """Assemble a CapabilityView — resolves rules fresh (use for single lookups)."""
        effective_rules = resolve_effective_rules(workspace_id, self._db, field=None)
        return self._build_view_with_rules(action, workspace_id, effective_rules)

    def _build_view_with_rules(
        self,
        action: ActionDefinition,
        workspace_id: int,
        effective_rules: list,
    ) -> CapabilityView:
        """Assemble a CapabilityView using a pre-resolved rule list (batch-safe)."""
        required_roles: set[str] = set()
        for rule in effective_rules:
            if rule.allowed_roles:
                required_roles.update(rule.allowed_roles)

        required_permissions: set[str] = set()
        for role in required_roles:
            required_permissions.update(get_permissions_for_role(role))

        linked = self.get_linked_workflows(action.name, workspace_id)

        return CapabilityView(
            action_id=action.id,
            name=action.name,
            display_name=action.display_name,
            description=action.description,
            aliases=list(action.aliases or []),
            workflow_type=action.workflow_type,
            required_roles=sorted(required_roles),
            required_permissions=sorted(required_permissions),
            input_schema=action.input_schema,
            output_schema=action.output_schema,
            linked_workflow_ids=linked,
            active=action.active,
        )
