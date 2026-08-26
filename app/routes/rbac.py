"""
app/routes/rbac.py

RBAC management endpoints.

  POST /rbac/extract/{workspace_id}    — trigger rule + role extraction from BRDs
  GET  /rbac/roles/{workspace_id}      — list role shapes for a workspace
  POST /rbac/assign                    — assign a user_id to a role shape
  GET  /rbac/me                        — what permissions does the caller have?

These endpoints are for admin/HR workflow. The permission check on every route
itself requires admin:manage_roles or region_manager and above.
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.rbac.rule_extractor import RuleExtractionService
from app.rbac.permission_checker import PermissionChecker
from app.models.role_assignment import RoleAssignment, VALID_ROLES
from app.models.workspace import Workspace
from app.repositories.audit_repo import create as audit_create
from app.models.audit_log import AUDIT_EVENT_RBAC_ASSIGNMENT

router = APIRouter(prefix="/rbac", tags=["rbac"])


def _require_user(
    x_user_id: str | None = Header(default=None),
    x_workspace_id: str | None = Header(default=None),
) -> tuple[str, int]:
    if not x_user_id:
        raise HTTPException(400, "X-User-Id header required")
    if not x_workspace_id:
        raise HTTPException(400, "X-Workspace-Id header required")
    try:
        return x_user_id, int(x_workspace_id)
    except ValueError:
        raise HTTPException(400, "X-Workspace-Id must be integer")


class AssignRoleRequest(BaseModel):
    user_id: str
    role: str
    workspace_id: int


@router.post("/extract/{workspace_id}")
def extract_rules_and_roles(
    workspace_id: int,
    db: Session = Depends(get_db),
    x_user_id: str | None = Header(default=None),
    x_workspace_id: str | None = Header(default=None),
):
    """Run RuleExtractionService for a workspace.

    Parses WorkflowBusinessRule text → BusinessRuleDefinition rows.
    Parses WorkflowActor names → RoleAssignment shapes (user_id=None).
    Idempotent — safe to call multiple times.
    """
    user_id, caller_ws = _require_user(x_user_id, x_workspace_id)

    checker = PermissionChecker(db)
    if not checker.can(user_id, "admin:manage_roles", caller_ws):
        # region_manager and above also acceptable
        if not checker.can(user_id, "rule:create", workspace_id):
            raise HTTPException(403, "Insufficient permissions")

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if workspace is None:
        raise HTTPException(404, f"Workspace {workspace_id} not found")

    svc = RuleExtractionService()
    result = svc.extract_for_workspace(db=db, workspace_id=workspace_id)
    return {"workspace_id": workspace_id, **result}


@router.get("/roles/{workspace_id}")
def list_role_shapes(
    workspace_id: int,
    db: Session = Depends(get_db),
    x_user_id: str | None = Header(default=None),
    x_workspace_id: str | None = Header(default=None),
):
    """List all role shapes for a workspace (including unassigned ones)."""
    user_id, caller_ws = _require_user(x_user_id, x_workspace_id)

    checker = PermissionChecker(db)
    if not checker.can(user_id, "audit:read", workspace_id):
        raise HTTPException(403, "Insufficient permissions: audit:read")

    rows = (
        db.query(RoleAssignment)
        .filter(
            RoleAssignment.workspace_id == workspace_id,
            RoleAssignment.active.is_(True),
        )
        .all()
    )

    return [
        {
            "id":             r.id,
            "role":           r.role,
            "user_id":        r.user_id,
            "workspace_id":   r.workspace_id,
            "source_rule_id": r.source_rule_id,
            "assigned":       r.user_id is not None,
        }
        for r in rows
    ]


@router.post("/assign")
def assign_role(
    body: AssignRoleRequest,
    db: Session = Depends(get_db),
    x_user_id: str | None = Header(default=None),
    x_workspace_id: str | None = Header(default=None),
):
    """Assign a real user_id to a role in a workspace.

    If a role shape (user_id=None) already exists for that role+workspace,
    it is updated. Otherwise a new RoleAssignment is created.
    """
    user_id, caller_ws = _require_user(x_user_id, x_workspace_id)

    checker = PermissionChecker(db)
    if not checker.can(user_id, "admin:manage_roles", caller_ws):
        raise HTTPException(403, "Insufficient permissions: admin:manage_roles")

    if body.role not in VALID_ROLES:
        raise HTTPException(400, f"Invalid role '{body.role}'. Valid: {sorted(VALID_ROLES)}")

    workspace = db.query(Workspace).filter(Workspace.id == body.workspace_id).first()
    if workspace is None:
        raise HTTPException(404, f"Workspace {body.workspace_id} not found")

    # Find existing unassigned shape for this role+workspace, or create new
    existing = (
        db.query(RoleAssignment)
        .filter(
            RoleAssignment.workspace_id == body.workspace_id,
            RoleAssignment.role == body.role,
            RoleAssignment.user_id.is_(None),
        )
        .first()
    )

    if existing:
        existing.user_id = body.user_id
        db.commit()
        ra_id = existing.id
    else:
        ra = RoleAssignment(
            user_id=body.user_id,
            role=body.role,
            workspace_id=body.workspace_id,
            active=True,
        )
        db.add(ra)
        db.commit()
        db.refresh(ra)
        ra_id = ra.id

    audit_create(
        db=db,
        workflow_id=None,
        action="rbac:assign",
        status="success",
        event_type=AUDIT_EVENT_RBAC_ASSIGNMENT,
        request_payload=str(body.model_dump()),
        response_payload=str({"role_assignment_id": ra_id}),
    )

    return {"role_assignment_id": ra_id, "user_id": body.user_id,
            "role": body.role, "workspace_id": body.workspace_id}


@router.get("/me")
def my_permissions(
    db: Session = Depends(get_db),
    x_user_id: str | None = Header(default=None),
    x_workspace_id: str | None = Header(default=None),
):
    """Return the caller's roles and effective permissions in their workspace."""
    user_id, workspace_id = _require_user(x_user_id, x_workspace_id)
    checker = PermissionChecker(db)
    roles   = checker.get_roles(user_id, workspace_id)
    perms   = checker.get_all_permissions(user_id, workspace_id)
    return {
        "user_id":      user_id,
        "workspace_id": workspace_id,
        "roles":        roles,
        "permissions":  sorted(perms),
    }
