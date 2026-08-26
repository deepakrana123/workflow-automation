"""
app/runtime/rbac_resolver.py

RBACCapabilityResolver — resolves which ActionDefinition IDs a user may
access, given their workspace, roles, and (optionally) an active workflow.

This is the RBAC boundary for retrieval scoping. It runs BEFORE the
retrieval pipeline so that the retrieval can filter to allowed actions,
rather than retrieving everything and checking permissions afterwards.

Three scope modes:
  1. Global scope  — user has capability:read; all active actions allowed
                     (no workflow context)
  2. Workflow scope — intersect global allowed set with the set of actions
                      referenced in the active workflow's DAG steps
  3. Step scope    — further intersect with actions valid at the current step
                     (based on step's action field and allowed_roles)

The resolver never grants permission — it only narrows the candidate set.
Final authorization is always re-checked by RuntimeOrchestrator before
execution.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.rbac.permission_checker import PermissionChecker
from app.models.action_definitions import ActionDefinition
from app.models.workflow import Workflow
from app.models.workflow_execution import WorkflowExecution
from app.runtime.context import RetrievalContext
from app.core.logger import logger


class RBACCapabilityResolver:
    """Resolve which action IDs a user is permitted to see/retrieve."""

    def __init__(self, db: Session):
        self._db = db
        self._checker = PermissionChecker(db)

    def resolve(self, ctx: RetrievalContext) -> RetrievalContext:
        """
        Populate ctx.allowed_action_ids and ctx.roles based on RBAC.

        Returns the same context object with allowed_action_ids filled in.
        - None  → not resolved (caller should treat as no restriction — rare)
        - set() → no actions allowed (permission denied)
        - {1,2,3,...} → exactly these IDs are permitted

        Does NOT raise. On any error returns ctx with allowed_action_ids=set()
        (fail closed).
        """
        try:
            # Resolve user roles once
            ctx.roles = self._checker.get_roles(ctx.user_id, ctx.workspace_id)

            # Check base capability:read permission
            if not self._checker.can(ctx.user_id, "capability:read", ctx.workspace_id):
                logger.info(
                    "rbac_resolver_no_capability_read",
                    extra={"extra_data": {
                        "user_id": ctx.user_id,
                        "workspace_id": ctx.workspace_id,
                    }},
                )
                ctx.allowed_action_ids = set()
                return ctx

            # Fetch all active action IDs (global pool)
            all_ids = self._get_all_active_action_ids()

            if not ctx.has_workflow_scope():
                # Global scope — all active actions
                ctx.allowed_action_ids = all_ids
                return ctx

            # Workflow scope — intersect with actions in the workflow's DAG
            workflow_action_ids = self._get_workflow_action_ids(ctx.workflow_id)
            if workflow_action_ids is None:
                # Workflow not found or no DAG — fall back to global
                ctx.allowed_action_ids = all_ids
                return ctx

            ctx.allowed_action_ids = all_ids & workflow_action_ids

            # Step scope — if current step is known, further narrow
            if ctx.has_step_scope() and ctx.workflow_id:
                step_action_ids = self._get_step_action_ids(
                    ctx.workflow_id, ctx.current_step_id, ctx.roles
                )
                if step_action_ids is not None:
                    ctx.allowed_action_ids = ctx.allowed_action_ids & step_action_ids

            return ctx

        except Exception as exc:
            logger.warning(
                "rbac_resolver_error",
                extra={"extra_data": {
                    "user_id":      ctx.user_id,
                    "workspace_id": ctx.workspace_id,
                    "error":        str(exc),
                }},
            )
            ctx.allowed_action_ids = set()
            return ctx

    # ── Private helpers ────────────────────────────────────────────────────────

    def _get_all_active_action_ids(self) -> set[int]:
        rows = (
            self._db.query(ActionDefinition.id)
            .filter(ActionDefinition.active.is_(True))
            .all()
        )
        return {r.id for r in rows}

    def _get_workflow_action_ids(self, workflow_id: int) -> set[int] | None:
        """Return IDs of ActionDefinitions used in the workflow's DAG steps."""
        workflow = (
            self._db.query(Workflow)
            .filter(Workflow.id == workflow_id)
            .first()
        )
        if workflow is None:
            return None

        steps = (workflow.parsed_rule_json or {}).get("steps", [])
        action_names = {s.get("action") for s in steps if s.get("action")}
        if not action_names:
            return set()

        rows = (
            self._db.query(ActionDefinition.id)
            .filter(
                ActionDefinition.name.in_(action_names),
                ActionDefinition.active.is_(True),
            )
            .all()
        )
        return {r.id for r in rows}

    def _get_step_action_ids(
        self,
        workflow_id: int,
        step_id: str,
        user_roles: list[str],
    ) -> set[int] | None:
        """
        For the specific step, return allowed action IDs considering step-level
        role restrictions.

        If the step has allowed_roles and the user doesn't match, returns empty set.
        If no role restriction on the step, returns the step's action ID only.
        """
        workflow = (
            self._db.query(Workflow)
            .filter(Workflow.id == workflow_id)
            .first()
        )
        if workflow is None:
            return None

        steps = (workflow.parsed_rule_json or {}).get("steps", [])
        step_def = next((s for s in steps if str(s.get("id")) == str(step_id)), None)
        if step_def is None:
            return None

        # Check step-level role restriction
        step_allowed_roles: list[str] = []
        for br in step_def.get("business_rules") or []:
            step_allowed_roles.extend(br.get("allowed_roles") or [])

        if step_allowed_roles:
            user_role_set = set(user_roles)
            allowed_role_set = set(step_allowed_roles)
            if not user_role_set.intersection(allowed_role_set):
                # User's roles don't satisfy this step
                return set()

        # Return the single action ID for this step
        action_name = step_def.get("action")
        if not action_name:
            return set()

        row = (
            self._db.query(ActionDefinition.id)
            .filter(
                ActionDefinition.name == action_name,
                ActionDefinition.active.is_(True),
            )
            .first()
        )
        return {row.id} if row else set()

    def can_execute_action(
        self,
        user_id: str,
        workspace_id: int,
        action_id: int,
        workflow_id: int | None = None,
        step_id: str | None = None,
    ) -> tuple[bool, str]:
        """
        Final authorization check before execution.

        Returns (allowed: bool, reason: str).
        Never trust a previously cached result for execution — always re-check.
        """
        try:
            if not self._checker.can(user_id, "capability:read", workspace_id):
                return False, "CAPABILITY_READ_DENIED"

            action = (
                self._db.query(ActionDefinition)
                .filter(ActionDefinition.id == action_id, ActionDefinition.active.is_(True))
                .first()
            )
            if action is None:
                return False, "ACTION_NOT_FOUND"

            if workflow_id is not None:
                workflow_ids = self._get_workflow_action_ids(workflow_id)
                if workflow_ids is not None and action_id not in workflow_ids:
                    return False, "ACTION_NOT_IN_WORKFLOW"

            if step_id is not None and workflow_id is not None:
                roles = self._checker.get_roles(user_id, workspace_id)
                step_ids = self._get_step_action_ids(workflow_id, step_id, roles)
                if step_ids is not None and action_id not in step_ids:
                    return False, "ROLE_NOT_ALLOWED_AT_STEP"

            return True, "ALLOWED"

        except Exception as exc:
            logger.warning(
                "rbac_can_execute_error",
                extra={"extra_data": {
                    "user_id":   user_id,
                    "action_id": action_id,
                    "error":     str(exc),
                }},
            )
            return False, "INTERNAL_ERROR"
