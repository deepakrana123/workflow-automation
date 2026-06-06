from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowResponse,
    DebugParseRequest,
)
from typing import List
from app.services import workflow_service
from app.core.logger import logger
from app.metrics.parser_metrics import parser_metrics

router = APIRouter(prefix="/workflows")


@router.post("/", response_model=WorkflowResponse)
def create_workflow(payload: WorkflowCreate, db: Session = Depends(get_db)):
    try:
        result = workflow_service.create_workflow_service(payload, db)
        return result
    except ValueError as e:
        print(e, "E")
        logger.warning(
            "route_create_workflow_failed",
            extra={
                "extra_data": {
                    "error": str(e),
                    "name": payload.name,
                    "domain": payload.domain,
                }
            },
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    try:
        return workflow_service.get_workflow_service(workflow_id, db)
    except ValueError as e:
        logger.warning(
            "route_get_workflow_not_found",
            extra={"extra_data": {"workflow_id": workflow_id}},
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[WorkflowResponse])
def get_all_worflow(domain: str | None = None, db: Session = Depends(get_db)):
    return workflow_service.list_workflow_service(domain, db)


@router.post("/debug-parse")
def debug_parse(payload: DebugParseRequest):
    return workflow_service.debug_parse_service(payload.raw_input)


@router.post("/metrics")
def metric_return():
    return parser_metrics.to_dict()
