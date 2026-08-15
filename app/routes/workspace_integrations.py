"""
app/routes/workspace_integrations.py

REST API for WorkspaceIntegration management.

Endpoints:
  GET    /workspaces/{workspace_id}/integrations
  POST   /workspaces/{workspace_id}/integrations
  GET    /workspace-integrations/{id}
  PUT    /workspace-integrations/{id}
  DELETE /workspace-integrations/{id}
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.workspace_integrations.integrations import WorkspaceIntegrationService
from app.schemas.workspace_integration import (
    WorkspaceIntegrationCreate,
    WorkspaceIntegrationUpdate,
    WorkspaceIntegrationResponse,
)
from app.core.logger import logger

router = APIRouter(tags=["workspace-integrations"])


# ── List ──────────────────────────────────────────────────────────────────────

@router.get(
    "/workspaces/{workspace_id}/integrations",
    response_model=list[WorkspaceIntegrationResponse],
)
def list_integrations(
    workspace_id: int,
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    svc = WorkspaceIntegrationService(db)
    try:
        return svc.list_by_workspace(workspace_id, active_only=active_only)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ── Create ────────────────────────────────────────────────────────────────────

@router.post(
    "/workspaces/{workspace_id}/integrations",
    response_model=WorkspaceIntegrationResponse,
    status_code=201,
)
def create_integration(
    workspace_id: int,
    payload: WorkspaceIntegrationCreate,
    db: Session = Depends(get_db),
):
    svc = WorkspaceIntegrationService(db)
    try:
        return svc.create(workspace_id, payload)
    except ValueError as exc:
        logger.warning(
            "route_create_integration_failed",
            extra={"extra_data": {
                "workspace_id": workspace_id,
                "error":        str(exc),
            }},
        )
        raise HTTPException(status_code=400, detail=str(exc))


# ── Get ───────────────────────────────────────────────────────────────────────

@router.get(
    "/workspace-integrations/{integration_id}",
    response_model=WorkspaceIntegrationResponse,
)
def get_integration(
    integration_id: int,
    db: Session = Depends(get_db),
):
    svc = WorkspaceIntegrationService(db)
    try:
        return svc.get(integration_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ── Update ────────────────────────────────────────────────────────────────────

@router.put(
    "/workspace-integrations/{integration_id}",
    response_model=WorkspaceIntegrationResponse,
)
def update_integration(
    integration_id: int,
    payload: WorkspaceIntegrationUpdate,
    db: Session = Depends(get_db),
):
    svc = WorkspaceIntegrationService(db)
    try:
        return svc.update(integration_id, payload)
    except ValueError as exc:
        logger.warning(
            "route_update_integration_failed",
            extra={"extra_data": {
                "integration_id": integration_id,
                "error":          str(exc),
            }},
        )
        raise HTTPException(status_code=400, detail=str(exc))


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete(
    "/workspace-integrations/{integration_id}",
    status_code=204,
)
def delete_integration(
    integration_id: int,
    db: Session = Depends(get_db),
):
    svc = WorkspaceIntegrationService(db)
    try:
        svc.delete(integration_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
