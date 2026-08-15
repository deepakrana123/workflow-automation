"""
app/routes/execute.py

Workflow execution endpoints: dispatch, pause, resume.
Delegates all business logic to WorkflowDispatchService.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.execute import ExecuteWorkflow
from app.services.workflow_dispatch_service import WorkflowDispatchService

router = APIRouter(prefix="/execute", tags=["execute"])


@router.post("/")
def publish_event(body: ExecuteWorkflow, db: Session = Depends(get_db)):
    svc = WorkflowDispatchService(db)
    try:
        result = svc.dispatch(
            workflow_id=body.workflow_id,
            entity_id=body.entity_id,
            event_type=getattr(body, "event_type", None),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if result.success:
        return {
            "success": True,
            "queued": True,
            "workflow_run_id": result.workflow_run_id,
            "workflow_execution_id": result.workflow_execution_id,
        }
    return {
        "success": False,
        "message": result.message,
        "workflow_execution_id": result.workflow_execution_id,
    }


@router.post("/{workflow_execution_id}/pause")
def pause_execution(
    workflow_execution_id: int, db: Session = Depends(get_db)
):
    svc = WorkflowDispatchService(db)
    try:
        return svc.pause(workflow_execution_id)
    except ValueError as e:
        status = 404 if "not found" in str(e) else 409
        raise HTTPException(status_code=status, detail=str(e))


@router.post("/{workflow_execution_id}/resume")
def resume_execution(
    workflow_execution_id: int, db: Session = Depends(get_db)
):
    svc = WorkflowDispatchService(db)
    try:
        return svc.resume(workflow_execution_id)
    except ValueError as e:
        status = 404 if "not found" in str(e) else 409
        raise HTTPException(status_code=status, detail=str(e))
