"""
app/routes/action_configurations.py

REST API for ActionConfiguration management.

Endpoints:
  GET    /workflows/{workflow_knowledge_id}/action-configurations
  GET    /action-configurations/{id}
  PUT    /action-configurations/{id}
  PATCH  /action-configurations/{id}/activate
  PATCH  /action-configurations/{id}/deactivate
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.action_configuration.management_service import ActionConfigurationManagementService
from app.schemas.action_configuration import (
    ActionConfigurationUpdate,
    ActionConfigurationResponse,
)
from app.core.logger import logger

router = APIRouter(tags=["action-configurations"])


# ── List by workflow ──────────────────────────────────────────────────────────

@router.get(
    "/workflows/{workflow_knowledge_id}/action-configurations",
    response_model=list[ActionConfigurationResponse],
)
def list_action_configurations(
    workflow_knowledge_id: int,
    db: Session = Depends(get_db),
):
    svc = ActionConfigurationManagementService(db)
    try:
        return svc.list_by_workflow(workflow_knowledge_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ── Get ───────────────────────────────────────────────────────────────────────

@router.get(
    "/action-configurations/{configuration_id}",
    response_model=ActionConfigurationResponse,
)
def get_action_configuration(
    configuration_id: int,
    db: Session = Depends(get_db),
):
    svc = ActionConfigurationManagementService(db)
    try:
        return svc.get(configuration_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ── Update — creates new version ─────────────────────────────────────────────

@router.put(
    "/action-configurations/{configuration_id}",
    response_model=ActionConfigurationResponse,
)
def update_action_configuration(
    configuration_id: int,
    payload: ActionConfigurationUpdate,
    db: Session = Depends(get_db),
):
    svc = ActionConfigurationManagementService(db)
    try:
        return svc.update(configuration_id, payload)
    except ValueError as exc:
        logger.warning(
            "route_update_action_configuration_failed",
            extra={"extra_data": {
                "configuration_id": configuration_id,
                "error":            str(exc),
            }},
        )
        raise HTTPException(status_code=400, detail=str(exc))


# ── Activate ──────────────────────────────────────────────────────────────────

@router.patch(
    "/action-configurations/{configuration_id}/activate",
    response_model=ActionConfigurationResponse,
)
def activate_action_configuration(
    configuration_id: int,
    db: Session = Depends(get_db),
):
    svc = ActionConfigurationManagementService(db)
    try:
        return svc.activate(configuration_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ── Deactivate ────────────────────────────────────────────────────────────────

@router.patch(
    "/action-configurations/{configuration_id}/deactivate",
    response_model=ActionConfigurationResponse,
)
def deactivate_action_configuration(
    configuration_id: int,
    db: Session = Depends(get_db),
):
    svc = ActionConfigurationManagementService(db)
    try:
        return svc.deactivate(configuration_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
