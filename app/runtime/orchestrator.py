"""
app/runtime/orchestrator.py

WorkflowRuntimeOrchestrator — the single service that connects all runtime
systems for a user query or action execution request.

Responsibilities (in order):
  1.  Resolve authenticated user + roles
  2.  Resolve workspace
  3.  Resolve active workflow/execution (if provided)
  4.  Build RetrievalContext
  5.  Resolve allowed capabilities from RBAC (RBACCapabilityResolver)
  6.  Run scoped retrieval (ScopedRetrievalService)
  7.  Validate selected candidate against RBAC (re-check — never trust retrieval)
  8.  Evaluate applicable rules (RuntimeRuleEngine)
  9.  Execute action via WorkflowDispatchService (if requested)
 10.  Record audit event
 11.  Return structured RuntimeResponse

Routes remain thin — all logic lives here.
LLM is never called here. Rule checks are deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Any

from sqlalchemy.orm import Session

from app.rbac.permission_checker import PermissionChecker
from app.models.workflow import Workflow
from app.models.workflow_execution import WorkflowExecution
from app.models.execution_step import ExecutionStep
from app.models.workspace import Workspace

from app.runtime.context import RetrievalContext, RuleEvaluationContext
from app.runtime.rbac_resolver import RBACCapabilityResolver
from app.runtime.rule_engine import RuntimeRuleEngine
from app.runtime.scoped_retrieval import ScopedRetrievalService, ScopedRetrievalResult
from app.runtime.audit import RuntimeAuditService

from app.core.logger import logger


# ── Response shape ─────────────────────────────────────────────────────────────

@dataclass
class RuntimeWorkflowInfo:
    id: int
    name: str
    status: str
    domain: str
    workspace_id: int | None
    step_count: int


@dataclass
class RuntimeExecutionInfo:
    id: int
    status: str
    current_step_id: str | None
    current_step_name: str | None
    started_at: str | None
    completed_at: str | None


@dataclass
class RuntimeActorInfo:
    user_id: str
    roles: list[str]
    workspace_id: int


@dataclass
class RuntimeAuthzInfo:
    allowed: bool
    reason: str | None = None


@dataclass
class RuntimeResponse:
    """Structured response returned to routes / chatbot clients."""

    workflow: Optional[RuntimeWorkflowInfo] = None
    execution: Optional[RuntimeExecutionInfo] = None
    actor: Optional[RuntimeActorInfo] = None
    retrieval: Optional[dict] = None
    authorization: Optional[RuntimeAuthzInfo] = None
    rules: Optional[dict] = None
    execution_result: Optional[dict] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        def _s(v):
            if v is None:
                return None
            if hasattr(v, "__dataclass_fields__"):
                return {k: _s(getattr(v, k)) for k in v.__dataclass_fields__}
            return v

        return {
            "workflow":          _s(self.workflow),
            "execution":         _s(self.execution),
            "actor":             _s(self.actor),
            "retrieval":         self.retrieval,
            "authorization":     _s(self.authorization),
            "rules":             self.rules,
            "execution_result":  self.execution_result,
            "error":             self.error,
        }


# ── Orchestrator ───────────────────────────────────────────────────────────────

class WorkflowRuntimeOrchestrator:
    """
    Central runtime coordinator. Instantiate per-request (stateless, thread-safe).
    """

    def __init__(
        self,
        db: Session,
        retrieval_service: ScopedRetrievalService | None = None,
    ):
        self._db = db
        self._checker = PermissionChecker(db)
        self._rbac = RBACCapabilityResolver(db)
        self._rules = RuntimeRuleEngine(db)
        self._retrieval = retrieval_service
        self._audit = RuntimeAuditService(db)

    # ── 1. Accessible workflows ────────────────────────────────────────────────

    def get_accessible_workflows(
        self, user_id: str, workspace_id: int
    ) -> list[RuntimeWorkflowInfo]:
        """Return workflows the user can access in their workspace."""
        self._audit.workflow_accessed(user_id, workspace_id, workflow_id=None)

        if not self._checker.can(user_id, "workflow:read", workspace_id):
            return []

        workflows = (
            self._db.query(Workflow)
            .filter(
                Workflow.workspace_id == workspace_id,
                Workflow.status.in_(["active", "published"]),
            )
            .order_by(Workflow.updated_at.desc())
            .all()
        )

        result = []
        for wf in workflows:
            steps = (wf.parsed_rule_json or {}).get("steps", [])
            result.append(RuntimeWorkflowInfo(
                id=wf.id,
                name=wf.name,
                status=wf.status,
                domain=wf.domain,
                workspace_id=wf.workspace_id,
                step_count=len(steps),
            ))
        return result

    def get_workflow_detail(
        self, user_id: str, workspace_id: int, workflow_id: int
    ) -> RuntimeResponse:
        """Return a single workflow with RBAC check."""
        resp = RuntimeResponse()

        if not self._checker.can(user_id, "workflow:read", workspace_id):
            resp.error = "Insufficient permissions: workflow:read"
            resp.authorization = RuntimeAuthzInfo(allowed=False, reason="WORKFLOW_READ_DENIED")
            return resp

        wf = self._db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if wf is None:
            resp.error = "Workflow not found"
            return resp

        if wf.workspace_id and wf.workspace_id != workspace_id:
            # Workspace isolation — don't leak other workspaces' workflows
            resp.error = "Workflow not found"
            return resp

        steps = (wf.parsed_rule_json or {}).get("steps", [])
        resp.workflow = RuntimeWorkflowInfo(
            id=wf.id,
            name=wf.name,
            status=wf.status,
            domain=wf.domain,
            workspace_id=wf.workspace_id,
            step_count=len(steps),
        )
        resp.actor = RuntimeActorInfo(
            user_id=user_id,
            roles=self._checker.get_roles(user_id, workspace_id),
            workspace_id=workspace_id,
        )
        resp.authorization = RuntimeAuthzInfo(allowed=True)
        return resp

    # ── 2. Execution state ─────────────────────────────────────────────────────

    def get_execution_state(
        self,
        user_id: str,
        workspace_id: int,
        execution_id: int,
    ) -> RuntimeResponse:
        """Return execution state with step details."""
        resp = RuntimeResponse()

        if not self._checker.can(user_id, "workflow:read", workspace_id):
            resp.error = "Insufficient permissions: workflow:read"
            resp.authorization = RuntimeAuthzInfo(allowed=False, reason="WORKFLOW_READ_DENIED")
            return resp

        execution = (
            self._db.query(WorkflowExecution)
            .filter(WorkflowExecution.id == execution_id)
            .first()
        )
        if execution is None:
            resp.error = "Execution not found"
            return resp

        # Verify workspace alignment — execution → workflow → workspace
        wf = self._db.query(Workflow).filter(Workflow.id == execution.workflow_id).first()
        if wf and wf.workspace_id and wf.workspace_id != workspace_id:
            if not self._checker.can(user_id, "audit:read", workspace_id):
                resp.error = "Execution not found"
                return resp

        # Current step
        current_step = (
            self._db.query(ExecutionStep)
            .filter(
                ExecutionStep.workflow_execution_id == execution_id,
                ExecutionStep.status.in_(["RUNNING", "WAITING", "BLOCKED"]),
            )
            .order_by(ExecutionStep.created_at.desc())
            .first()
        )

        resp.execution = RuntimeExecutionInfo(
            id=execution.id,
            status=execution.status,
            current_step_id=current_step.step_id if current_step else None,
            current_step_name=current_step.step_name if current_step else None,
            started_at=execution.started_at.isoformat() if execution.started_at else None,
            completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
        )

        if wf:
            steps = (wf.parsed_rule_json or {}).get("steps", [])
            resp.workflow = RuntimeWorkflowInfo(
                id=wf.id,
                name=wf.name,
                status=wf.status,
                domain=wf.domain,
                workspace_id=wf.workspace_id,
                step_count=len(steps),
            )

        resp.actor = RuntimeActorInfo(
            user_id=user_id,
            roles=self._checker.get_roles(user_id, workspace_id),
            workspace_id=workspace_id,
        )
        resp.authorization = RuntimeAuthzInfo(allowed=True)
        return resp

    # ── 3. Scoped retrieval ────────────────────────────────────────────────────

    def retrieve(
        self,
        user_id: str,
        workspace_id: int,
        query: str,
        workflow_id: int | None = None,
        execution_id: int | None = None,
        top_k: int = 10,
        include_diagnostics: bool = False,
    ) -> RuntimeResponse:
        """
        Scoped retrieval: RBAC scope → retrieval → authorization filter → result.

        The server derives permissions from user_id + workspace_id.
        Client-provided role claims are ignored.
        """
        resp = RuntimeResponse()

        # Base permission check
        if not self._checker.can(user_id, "capability:read", workspace_id):
            resp.error = "Insufficient permissions: capability:read"
            resp.authorization = RuntimeAuthzInfo(allowed=False, reason="CAPABILITY_READ_DENIED")
            self._audit.authorization_denied(user_id, workspace_id, None, "CAPABILITY_READ_DENIED", workflow_id)
            return resp

        # Build context
        current_step_id = None
        if execution_id is not None:
            current_step_id = self._get_current_step_id(execution_id)

        ctx = RetrievalContext(
            user_id=user_id,
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            workflow_execution_id=execution_id,
            current_step_id=current_step_id,
        )

        # Resolve RBAC scope
        ctx = self._rbac.resolve(ctx)

        # Log retrieval start
        self._audit.retrieval_started(user_id, workspace_id, query, workflow_id)

        if self._retrieval is None:
            resp.error = "Retrieval service not available"
            return resp

        # Run scoped retrieval
        result: ScopedRetrievalResult = self._retrieval.retrieve(
            query=query,
            ctx=ctx,
            top_k=top_k,
            include_unauthorized_diagnostics=include_diagnostics,
        )

        # Log retrieval completion
        self._audit.retrieval_completed(
            user_id, workspace_id, query,
            result.total_retrieved, result.total_authorized,
            result.selected_action_name, workflow_id,
        )

        # Build retrieval section of response
        resp.retrieval = {
            "query":              query,
            "candidate_count":    result.total_retrieved,
            "authorized_count":   result.total_authorized,
            "selected_action_id": result.selected_action_id,
            "selected_action":    result.selected_action_name,
            "top_candidates": [
                {
                    "rank":           sc.final_rank,
                    "action_id":      sc.action_id,
                    "action_name":    sc.action_name,
                    "display_name":   sc.display_name,
                    "description":    sc.description,
                    "workflow_type":  sc.workflow_type,
                    "vector_rank":    sc.vector_rank,
                    "bm25_rank":      sc.bm25_rank,
                    "postgres_rank":  sc.postgres_rank,
                    "rrf_score":      round(sc.rrf_score, 5),
                    "authorized":     sc.authorized,
                }
                for sc in result.candidates
            ],
        }

        if include_diagnostics and result.diagnostics:
            resp.retrieval["diagnostics"] = [
                {
                    "action_id":         sc.action_id,
                    "action_name":       sc.action_name,
                    "authorized":        sc.authorized,
                    "rejection_reason":  sc.rejection_reason,
                    "rrf_score":         round(sc.rrf_score, 5),
                    "vector_rank":       sc.vector_rank,
                    "bm25_rank":         sc.bm25_rank,
                    "postgres_rank":     sc.postgres_rank,
                }
                for sc in result.diagnostics
            ]

        resp.actor = RuntimeActorInfo(
            user_id=user_id,
            roles=ctx.roles,
            workspace_id=workspace_id,
        )
        resp.authorization = RuntimeAuthzInfo(allowed=True)
        return resp

    # ── 4. Execute action ──────────────────────────────────────────────────────

    def execute_action(
        self,
        user_id: str,
        workspace_id: int,
        action_id: int,
        workflow_id: int | None = None,
        execution_id: int | None = None,
        step_id: str | None = None,
        request_data: dict | None = None,
        previous_step_outputs: dict | None = None,
    ) -> RuntimeResponse:
        """
        Full pre-execution pipeline:
          1. RBAC re-check (never trust cached/client state)
          2. Rule engine evaluation
          3. Dispatch (WorkflowDispatchService or direct action execution)
          4. Audit
        """
        resp = RuntimeResponse()
        roles = self._checker.get_roles(user_id, workspace_id)

        resp.actor = RuntimeActorInfo(
            user_id=user_id,
            roles=roles,
            workspace_id=workspace_id,
        )

        # ── Step 1: RBAC re-check ─────────────────────────────────────────────
        allowed, reason = self._rbac.can_execute_action(
            user_id=user_id,
            workspace_id=workspace_id,
            action_id=action_id,
            workflow_id=workflow_id,
            step_id=step_id,
        )
        resp.authorization = RuntimeAuthzInfo(allowed=allowed, reason=reason)

        if not allowed:
            self._audit.authorization_denied(user_id, workspace_id, action_id, reason, workflow_id)
            resp.error = f"Authorization denied: {reason}"
            return resp

        # ── Step 2: Rule engine ───────────────────────────────────────────────
        rule_ctx = RuleEvaluationContext(
            user_id=user_id,
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            workflow_execution_id=execution_id,
            step_id=step_id,
            action_id=action_id,
            actor_roles=roles,
            request_data=request_data or {},
            previous_step_outputs=previous_step_outputs or {},
        )
        rule_result = self._rules.evaluate(rule_ctx)
        resp.rules = rule_result.to_dict()

        self._audit.rule_evaluated(
            user_id, workspace_id,
            rule_result.allowed,
            len(rule_result.failed_rules),
            workflow_id,
        )

        if not rule_result.allowed:
            resp.error = "Rule engine blocked execution"
            return resp

        # ── Step 3: Execute ───────────────────────────────────────────────────
        # For workflow-scoped execution, dispatch via WorkflowDispatchService.
        # For direct action execution (no workflow), record as executed.
        if workflow_id is not None and execution_id is None:
            # Dispatch a new workflow execution
            from app.services.workflow_dispatch_service import WorkflowDispatchService
            dispatch_svc = WorkflowDispatchService(self._db)
            try:
                result = dispatch_svc.dispatch(
                    workflow_id=workflow_id,
                    entity_id=str(user_id),
                )
                resp.execution_result = {
                    "status":               "dispatched",
                    "workflow_execution_id": result.workflow_execution_id,
                    "message":              result.message or "Workflow queued",
                    "success":              result.success,
                }
                self._audit.action_executed(
                    user_id, workspace_id, f"workflow:{workflow_id}",
                    result.success, workflow_id, result.workflow_execution_id,
                )
            except Exception as exc:
                resp.execution_result = {"status": "failed", "error": str(exc)}
                self._audit.action_executed(
                    user_id, workspace_id, f"workflow:{workflow_id}",
                    False, workflow_id,
                )
                resp.error = f"Execution failed: {exc}"
        else:
            # Direct action execution (capability call without workflow)
            resp.execution_result = {
                "status":    "authorized",
                "action_id": action_id,
                "note":      "Action authorized; integrate with executor for direct invocation.",
            }
            self._audit.action_executed(
                user_id, workspace_id, f"action:{action_id}", True, workflow_id,
            )

        if workflow_id:
            wf = self._db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if wf:
                steps = (wf.parsed_rule_json or {}).get("steps", [])
                resp.workflow = RuntimeWorkflowInfo(
                    id=wf.id, name=wf.name, status=wf.status,
                    domain=wf.domain, workspace_id=wf.workspace_id,
                    step_count=len(steps),
                )

        return resp

    # ── 5. Global search ───────────────────────────────────────────────────────

    def global_search(
        self,
        user_id: str,
        workspace_id: int,
        query: str,
        top_k: int = 10,
    ) -> RuntimeResponse:
        """
        Permission-scoped global search — no workflow context.
        Returns all allowed actions matching the query.
        """
        resp = RuntimeResponse()

        if not self._checker.can(user_id, "capability:read", workspace_id):
            resp.error = "Insufficient permissions: capability:read"
            resp.authorization = RuntimeAuthzInfo(allowed=False, reason="CAPABILITY_READ_DENIED")
            return resp

        ctx = RetrievalContext(
            user_id=user_id,
            workspace_id=workspace_id,
            # No workflow scope — global search
        )
        ctx = self._rbac.resolve(ctx)

        if self._retrieval is None:
            resp.error = "Retrieval service not available"
            return resp

        result: ScopedRetrievalResult = self._retrieval.retrieve(
            query=query,
            ctx=ctx,
            top_k=top_k,
            include_unauthorized_diagnostics=False,
        )

        self._audit.global_search(user_id, workspace_id, query, result.total_authorized)

        resp.retrieval = {
            "query":            query,
            "scope":            "global",
            "candidate_count":  result.total_retrieved,
            "authorized_count": result.total_authorized,
            "top_candidates": [
                {
                    "rank":          sc.final_rank,
                    "action_id":     sc.action_id,
                    "action_name":   sc.action_name,
                    "display_name":  sc.display_name,
                    "description":   sc.description,
                    "workflow_type": sc.workflow_type,
                    "rrf_score":     round(sc.rrf_score, 5),
                }
                for sc in result.candidates
            ],
        }
        resp.actor = RuntimeActorInfo(
            user_id=user_id, roles=ctx.roles, workspace_id=workspace_id,
        )
        resp.authorization = RuntimeAuthzInfo(allowed=True)
        return resp

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _get_current_step_id(self, execution_id: int) -> str | None:
        step = (
            self._db.query(ExecutionStep)
            .filter(
                ExecutionStep.workflow_execution_id == execution_id,
                ExecutionStep.status.in_(["RUNNING", "WAITING", "BLOCKED"]),
            )
            .order_by(ExecutionStep.created_at.desc())
            .first()
        )
        return step.step_id if step else None
