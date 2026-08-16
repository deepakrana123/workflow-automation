"""
app/routes/workspaces.py

Workspace-level endpoints.

Currently exposes the multi-BRD knowledge synthesis (aggregated, deduplicated,
provenance-rich view across all BRDs in a workspace). Workspace CRUD will live
here too.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.workspace import Workspace
from pydantic import BaseModel

from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse
from app.services import nl_workflow_service
from app.workflow.workspace_context import WorkspaceContextService
from app.workflow.workspace_diagnostics import WorkspaceDiagnosticsService
from app.workflow.workspace_synthesis import WorkspaceSynthesisService
from app.workflow.workspace_workflow_synthesizer import WorkspaceWorkflowSynthesizer

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def _require_workspace(db: Session, workspace_id: int) -> Workspace:
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    return workspace


class SynthesizeWorkflowRequest(BaseModel):
    name: str
    domain: str  # finance | health | support


class GenerateWorkflowRequest(BaseModel):
    name: str
    user_request: str
    domain: str = "finance"
    selected_action_ids: list[int] = []


@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(active_only: bool = True, db: Session = Depends(get_db)):
    """List workspaces (active by default)."""
    query = db.query(Workspace)
    if active_only:
        query = query.filter(Workspace.active.is_(True))
    return query.order_by(Workspace.id.asc()).all()


@router.post("", response_model=WorkspaceResponse, status_code=201)
def create_workspace(body: WorkspaceCreate, db: Session = Depends(get_db)):
    """Create a workspace (one banking project)."""
    workspace = Workspace(
        name=body.name,
        display_name=body.display_name,
        description=body.description,
        organization_name=body.organization_name,
        active=True,
    )
    db.add(workspace)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Workspace name '{body.name}' already exists.",
        )
    db.refresh(workspace)
    return workspace


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(workspace_id: int, db: Session = Depends(get_db)):
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    return workspace


@router.get("/{workspace_id}/overview")
def get_workspace_overview(workspace_id: int, db: Session = Depends(get_db)):
    """Workspace header + headline counts (BRDs, actions, triggers, rules...).

    Read-only projection over existing knowledge — the first thing the user sees
    when opening a workspace.
    """
    _require_workspace(db, workspace_id)
    return WorkspaceContextService().overview(db, workspace_id)


@router.get("/{workspace_id}/documents")
def get_workspace_documents(workspace_id: int, db: Session = Depends(get_db)):
    """Per-BRD view: name, derived extraction/mapping status, and item counts.

    Lets the user inspect what MFlows understood from each uploaded BRD.
    """
    _require_workspace(db, workspace_id)
    return WorkspaceContextService().documents(db, workspace_id)


@router.get("/{workspace_id}/business-rules")
def get_workspace_business_rules(workspace_id: int, db: Session = Depends(get_db)):
    """The business rules MFlows extracted across all BRDs, with source document.

    Surfaced before generation for banking explainability.
    """
    _require_workspace(db, workspace_id)
    return WorkspaceContextService().business_rules(db, workspace_id)


@router.get("/{workspace_id}/actions")
def get_workspace_actions(workspace_id: int, db: Session = Depends(get_db)):
    """Workspace-scoped actions (deduplicated) + unresolved terms.

    This is the candidate action set for workspace-scoped generation. It does
    NOT include the global catalog — global actions are added explicitly.
    """
    _require_workspace(db, workspace_id)
    return WorkspaceContextService().actions(db, workspace_id)


@router.get("/{workspace_id}/diagnostics")
def get_workspace_diagnostics(workspace_id: int, db: Session = Depends(get_db)):
    """Full per-action pipeline trace for every BRD in the workspace.

    For each extracted action returns: extract_name, query_text, status,
    confidence, matched_action, top_candidates (top-K with scores), and
    diagnostic_classification (MAPPED / RETRIEVAL_MISS / MAPPING_REJECTED / PENDING).
    """
    _require_workspace(db, workspace_id)
    return WorkspaceDiagnosticsService().for_workspace(db, workspace_id)


@router.get("/{workspace_id}/synthesis")
def get_workspace_synthesis(workspace_id: int, db: Session = Depends(get_db)):
    """Aggregate all BRD knowledge in a workspace into one deduplicated view.

    Actions are deduplicated by their canonical ActionDefinition; each carries
    the BRDs that contributed it (source clause + confidence). Unresolved and
    low-confidence items are flagged for review.
    """
    workspace = (
        db.query(Workspace).filter(Workspace.id == workspace_id).first()
    )
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    return WorkspaceSynthesisService().for_workspace(db, workspace_id)


@router.post("/{workspace_id}/synthesize")
def synthesize_workspace_workflow(
    workspace_id: int,
    body: SynthesizeWorkflowRequest,
    db: Session = Depends(get_db),
):
    """Compile one executable workflow from all mapped actions in the workspace.

    Deterministic: aggregate + dedup across BRDs -> sequential DAG -> compile.
    Returns the created workflow with cross-BRD provenance per step.
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    try:
        return WorkspaceWorkflowSynthesizer().synthesize(
            db=db,
            workspace_id=workspace_id,
            name=body.name,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{workspace_id}/generate")
def generate_workspace_workflow(
    workspace_id: int,
    body: GenerateWorkflowRequest,
    db: Session = Depends(get_db),
):
    """Generate a workflow with AI, grounded in this workspace's context.

    Uses ONLY the workspace's mapped actions/triggers (+ any explicitly selected
    global actions) and the workspace business rules — never the full global
    catalog. Distinct from /synthesize (deterministic, no LLM).
    """
    _require_workspace(db, workspace_id)
    try:
        return nl_workflow_service.generate_workspace_workflow_service(
            db=db,
            workspace_id=workspace_id,
            name=body.name,
            user_request=body.user_request,
            domain=body.domain,
            selected_action_ids=body.selected_action_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError:
        raise HTTPException(status_code=502, detail="LLM generation failed")
