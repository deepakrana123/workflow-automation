"""
app/routes/capabilities.py

Capability discovery endpoints.

Search / list flow:
  Retrieval → CapabilityService.filter_by_permission → CapabilityView[]

The retrieval pipeline is NOT called here for simplicity of the first
increment. The catalog search is used for capability lookup. The full
retrieval → capability → permission → dispatch flow is wired when
the chat/search frontend calls this endpoint.

Endpoints:
  GET  /capabilities                  — list all capabilities the caller can see
  GET  /capabilities/{action_name}    — single capability
  POST /capabilities/search           — filter + RBAC-aware search

RBAC:
  All endpoints require X-User-Id and X-Workspace-Id headers.
  If missing, 400 is returned.  If user lacks capability:read, 403.

  In production these headers would come from a JWT middleware.
  For now the convention is explicit headers so the system can be
  exercised without building auth infrastructure first.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.capabilities.service import CapabilityService
from app.rbac.permission_checker import PermissionChecker

router = APIRouter(prefix="/capabilities", tags=["capabilities"])


def _get_caller(
    x_user_id: str | None = Header(default=None),
    x_workspace_id: str | None = Header(default=None),
) -> tuple[str, int]:
    """Extract caller identity from headers. 400 if missing."""
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-Id header required")
    if not x_workspace_id:
        raise HTTPException(status_code=400, detail="X-Workspace-Id header required")
    try:
        ws_id = int(x_workspace_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="X-Workspace-Id must be an integer")
    return x_user_id, ws_id


class CapabilitySearchRequest(BaseModel):
    query: str
    top_k: int = 10


@router.get("")
def list_capabilities(
    workflow_type: str | None = Query(None),
    db: Session = Depends(get_db),
    x_user_id: str | None = Header(default=None),
    x_workspace_id: str | None = Header(default=None),
):
    """List all capabilities the caller is permitted to see in their workspace."""
    user_id, workspace_id = _get_caller(x_user_id, x_workspace_id)

    checker = PermissionChecker(db)
    if not checker.can(user_id, "capability:read", workspace_id):
        raise HTTPException(status_code=403, detail="Insufficient permissions: capability:read")

    svc = CapabilityService(db)
    caps = svc.get_for_user(user_id, workspace_id)

    if workflow_type:
        caps = [c for c in caps if c.workflow_type == workflow_type]

    return [c.to_dict() for c in caps]


@router.get("/{action_name}")
def get_capability(
    action_name: str,
    db: Session = Depends(get_db),
    x_user_id: str | None = Header(default=None),
    x_workspace_id: str | None = Header(default=None),
):
    """Get a single capability by action name."""
    user_id, workspace_id = _get_caller(x_user_id, x_workspace_id)

    checker = PermissionChecker(db)
    if not checker.can(user_id, "capability:read", workspace_id):
        raise HTTPException(status_code=403, detail="Insufficient permissions: capability:read")

    svc = CapabilityService(db)
    cap = svc.get_by_action_name(action_name, workspace_id)
    if cap is None:
        raise HTTPException(status_code=404, detail=f"Capability '{action_name}' not found")

    return cap.to_dict()


@router.post("/search")
def search_capabilities(
    body: CapabilitySearchRequest,
    db: Session = Depends(get_db),
    x_user_id: str | None = Header(default=None),
    x_workspace_id: str | None = Header(default=None),
):
    """Text-search capabilities (alias/name match) filtered by RBAC.

    Uses the existing catalog text similarity search, then wraps results
    in CapabilityView and applies permission filtering.
    Does NOT call the retrieval pipeline (vector/BM25) — that is a separate
    evaluation track. This keeps retrieval improvement independent.
    """
    user_id, workspace_id = _get_caller(x_user_id, x_workspace_id)

    checker = PermissionChecker(db)
    if not checker.can(user_id, "capability:read", workspace_id):
        raise HTTPException(status_code=403, detail="Insufficient permissions: capability:read")

    from app.models.action_definitions import ActionDefinition
    from app.core.text_similarity import text_similarity

    query   = body.query.strip()
    top_k   = min(body.top_k, 20)
    actions = (
        db.query(ActionDefinition)
        .filter(ActionDefinition.active.is_(True))
        .all()
    )

    scored = []
    for a in actions:
        score = max(
            text_similarity(a.name.replace("_", " "), query),
            text_similarity(a.display_name or "", query),
            *[text_similarity(al, query) for al in (a.aliases or [])],
        )
        if score > 0.1:
            scored.append((score, a))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_actions = [a for _, a in scored[:top_k]]

    svc  = CapabilityService(db)
    # Resolve rules once for the batch — not per action
    from app.rbac.rule_inheritance import resolve_effective_rules as _rer
    eff_rules = _rer(workspace_id, db)
    caps = [svc._build_view_with_rules(a, workspace_id, eff_rules) for a in top_actions]

    return [c.to_dict() for c in caps]
