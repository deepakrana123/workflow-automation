"""
app/routes/runtime.py

Integrated Runtime API — all /api/runtime/* endpoints.

Authentication: X-User-Id + X-Workspace-Id headers (same convention as existing routes).
The server derives all permissions from these identities — client-supplied role
claims are ignored.

Endpoints:
  GET  /runtime/workflows                   — accessible workflows
  GET  /runtime/workflows/{workflow_id}     — single workflow detail
  GET  /runtime/executions/{execution_id}  — execution state
  GET  /runtime/executions/{execution_id}/steps — step detail list
  POST /runtime/retrieve                    — scoped retrieval
  POST /runtime/execute                     — execute action with RBAC+rules guard
  POST /runtime/search                      — global permission-scoped search
  GET  /runtime/rbac/me                     — my effective permissions (for RBAC inspector)
  GET  /runtime/rules/{workspace_id}        — effective rules (for Rule inspector)
"""

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.runtime.dependencies import get_orchestrator
from app.runtime.orchestrator import WorkflowRuntimeOrchestrator
from app.rbac.permission_checker import PermissionChecker
from app.rbac.rule_inheritance import resolve_effective_rules
from app.models.execution_step import ExecutionStep
from app.models.workflow_execution import WorkflowExecution
from app.core.logger import logger

router = APIRouter(prefix="/runtime", tags=["runtime"])


# ── Caller identity dependency ─────────────────────────────────────────────────

def _require_caller(
    x_user_id: Optional[str] = Header(default=None),
    x_workspace_id: Optional[str] = Header(default=None),
) -> tuple[str, int]:
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-Id header required")
    if not x_workspace_id:
        raise HTTPException(status_code=400, detail="X-Workspace-Id header required")
    try:
        return x_user_id, int(x_workspace_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="X-Workspace-Id must be an integer")


# ── Request bodies ─────────────────────────────────────────────────────────────

class RetrieveRequest(BaseModel):
    query: str
    workflow_id: Optional[int] = None
    execution_id: Optional[int] = None
    top_k: int = 10
    include_diagnostics: bool = False


class ExecuteRequest(BaseModel):
    action_id: int
    workflow_id: Optional[int] = None
    execution_id: Optional[int] = None
    step_id: Optional[str] = None
    request_data: dict = {}
    previous_step_outputs: dict = {}


class GlobalSearchRequest(BaseModel):
    query: str
    scope: str = "global"
    top_k: int = 10


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/workflows")
def list_accessible_workflows(
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default=None),
    x_workspace_id: Optional[str] = Header(default=None),
):
    """Return workflows the authenticated user can access in their workspace."""
    user_id, workspace_id = _require_caller(x_user_id, x_workspace_id)
    orch: WorkflowRuntimeOrchestrator = get_orchestrator(db)
    workflows = orch.get_accessible_workflows(user_id, workspace_id)
    return {
        "user_id":      user_id,
        "workspace_id": workspace_id,
        "workflows":    [
            {
                "id":           wf.id,
                "name":         wf.name,
                "status":       wf.status,
                "domain":       wf.domain,
                "workspace_id": wf.workspace_id,
                "step_count":   wf.step_count,
            }
            for wf in workflows
        ],
        "count": len(workflows),
    }


@router.get("/workflows/{workflow_id}")
def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default=None),
    x_workspace_id: Optional[str] = Header(default=None),
):
    """Return a single workflow with RBAC check."""
    user_id, workspace_id = _require_caller(x_user_id, x_workspace_id)
    orch = get_orchestrator(db)
    resp = orch.get_workflow_detail(user_id, workspace_id, workflow_id)
    if resp.error:
        code = 403 if resp.authorization and not resp.authorization.allowed else 404
        raise HTTPException(status_code=code, detail=resp.error)
    return resp.to_dict()


@router.get("/executions/{execution_id}")
def get_execution_state(
    execution_id: int,
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default=None),
    x_workspace_id: Optional[str] = Header(default=None),
):
    """Return execution state including current step."""
    user_id, workspace_id = _require_caller(x_user_id, x_workspace_id)
    orch = get_orchestrator(db)
    resp = orch.get_execution_state(user_id, workspace_id, execution_id)
    if resp.error:
        code = 403 if resp.authorization and not resp.authorization.allowed else 404
        raise HTTPException(status_code=code, detail=resp.error)
    return resp.to_dict()


@router.get("/executions/{execution_id}/steps")
def get_execution_steps(
    execution_id: int,
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default=None),
    x_workspace_id: Optional[str] = Header(default=None),
):
    """Return all steps for an execution with status and output."""
    user_id, workspace_id = _require_caller(x_user_id, x_workspace_id)

    checker = PermissionChecker(db)
    if not checker.can(user_id, "workflow:read", workspace_id):
        raise HTTPException(status_code=403, detail="Insufficient permissions: workflow:read")

    execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.id == execution_id
    ).first()
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")

    steps = (
        db.query(ExecutionStep)
        .filter(ExecutionStep.workflow_execution_id == execution_id)
        .order_by(ExecutionStep.created_at)
        .all()
    )

    def _step_dict(s: ExecutionStep) -> dict:
        return {
            "id":             str(s.id),
            "step_id":        s.step_id,
            "step_name":      s.step_name,
            "status":         s.status,
            "started_at":     s.started_at.isoformat() if s.started_at else None,
            "completed_at":   s.completed_at.isoformat() if s.completed_at else None,
            "attempts":       s.attempts,
            "last_error":     s.last_error,
            "rule_evaluation": (s.output_payload or {}).get("rule_evaluations"),
        }

    return {
        "execution_id": execution_id,
        "execution_status": execution.status,
        "steps": [_step_dict(s) for s in steps],
        "step_count": len(steps),
    }


@router.post("/retrieve")
def scoped_retrieve(
    body: RetrieveRequest,
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default=None),
    x_workspace_id: Optional[str] = Header(default=None),
):
    """
    Scoped retrieval — workflow + RBAC aware.

    The server resolves user permissions from X-User-Id + X-Workspace-Id.
    include_diagnostics requires audit:read permission.
    """
    user_id, workspace_id = _require_caller(x_user_id, x_workspace_id)

    # Diagnostics require elevated permission
    include_diag = body.include_diagnostics
    if include_diag:
        checker = PermissionChecker(db)
        if not checker.can(user_id, "audit:read", workspace_id):
            include_diag = False  # Silently downgrade — don't leak that diagnostics exist

    orch = get_orchestrator(db)
    resp = orch.retrieve(
        user_id=user_id,
        workspace_id=workspace_id,
        query=body.query,
        workflow_id=body.workflow_id,
        execution_id=body.execution_id,
        top_k=body.top_k,
        include_diagnostics=include_diag,
    )

    if resp.error and resp.authorization and not resp.authorization.allowed:
        raise HTTPException(status_code=403, detail=resp.error)

    return resp.to_dict()


@router.post("/execute")
def execute_action(
    body: ExecuteRequest,
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default=None),
    x_workspace_id: Optional[str] = Header(default=None),
):
    """
    Execute an action with full RBAC + rule engine guard.

    The backend:
    1. Re-checks RBAC (never trusts client state)
    2. Evaluates all applicable rules
    3. Dispatches only if both pass
    """
    user_id, workspace_id = _require_caller(x_user_id, x_workspace_id)

    orch = get_orchestrator(db)
    resp = orch.execute_action(
        user_id=user_id,
        workspace_id=workspace_id,
        action_id=body.action_id,
        workflow_id=body.workflow_id,
        execution_id=body.execution_id,
        step_id=body.step_id,
        request_data=body.request_data,
        previous_step_outputs=body.previous_step_outputs,
    )

    if resp.authorization and not resp.authorization.allowed:
        raise HTTPException(status_code=403, detail=resp.error or "Authorization denied")
    if resp.rules and not resp.rules.get("allowed"):
        raise HTTPException(
            status_code=422,
            detail={
                "message":      "Rule engine blocked execution",
                "failed_rules": resp.rules.get("failed_rules", []),
                "warnings":     resp.rules.get("warnings", []),
            },
        )

    return resp.to_dict()


@router.post("/search")
def global_search(
    body: GlobalSearchRequest,
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default=None),
    x_workspace_id: Optional[str] = Header(default=None),
):
    """
    Permission-scoped global capability search.

    Distinct from /retrieve (which is workflow-context-aware).
    Global search returns all allowed actions without workflow scope.
    """
    user_id, workspace_id = _require_caller(x_user_id, x_workspace_id)

    orch = get_orchestrator(db)
    resp = orch.global_search(
        user_id=user_id,
        workspace_id=workspace_id,
        query=body.query,
        top_k=body.top_k,
    )

    if resp.error and resp.authorization and not resp.authorization.allowed:
        raise HTTPException(status_code=403, detail=resp.error)

    return resp.to_dict()


@router.get("/rbac/me")
def my_runtime_permissions(
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default=None),
    x_workspace_id: Optional[str] = Header(default=None),
):
    """
    Return the caller's full RBAC profile for the RBAC Inspector screen.

    Includes roles, permissions, accessible workflow count, and allowed action count.
    """
    user_id, workspace_id = _require_caller(x_user_id, x_workspace_id)

    checker = PermissionChecker(db)
    roles = checker.get_roles(user_id, workspace_id)
    permissions = sorted(checker.get_all_permissions(user_id, workspace_id))

    # Count accessible workflows
    from app.models.workflow import Workflow
    from app.rbac.permission_checker import PermissionChecker as _PC
    orch = get_orchestrator(db)
    accessible_wf = orch.get_accessible_workflows(user_id, workspace_id)

    # Count allowed actions
    from app.runtime.rbac_resolver import RBACCapabilityResolver
    from app.runtime.context import RetrievalContext
    resolver = RBACCapabilityResolver(db)
    ctx = RetrievalContext(user_id=user_id, workspace_id=workspace_id)
    ctx = resolver.resolve(ctx)
    allowed_action_count = len(ctx.allowed_action_ids) if ctx.allowed_action_ids is not None else "all"

    return {
        "user_id":              user_id,
        "workspace_id":         workspace_id,
        "roles":                roles,
        "permissions":          permissions,
        "accessible_workflows": len(accessible_wf),
        "allowed_action_count": allowed_action_count,
    }


@router.get("/rules/{workspace_id}")
def get_effective_rules(
    workspace_id: int,
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default=None),
    x_workspace_id: Optional[str] = Header(default=None),
):
    """
    Return the effective rule set for a workspace (for the Rule Inspector screen).

    Requires audit:read or rule:read permission.
    """
    user_id, caller_ws = _require_caller(x_user_id, x_workspace_id)

    checker = PermissionChecker(db)
    if not (checker.can(user_id, "audit:read", workspace_id) or
            checker.can(user_id, "rule:read", workspace_id)):
        raise HTTPException(status_code=403, detail="Insufficient permissions: rule:read")

    rules = resolve_effective_rules(workspace_id, db)

    return {
        "workspace_id": workspace_id,
        "rule_count":   len(rules),
        "rules": [
            {
                "id":           r.id,
                "description":  r.description,
                "field":        r.field,
                "op":           r.op,
                "value":        r.value,
                "allowed_roles": r.allowed_roles,
                "locked":        r.locked,
                "evaluable":     r.is_evaluable(),
                "scope_workspace_id": r.scope_workspace_id,
            }
            for r in rules
        ],
    }
