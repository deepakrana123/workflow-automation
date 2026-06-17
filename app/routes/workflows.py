from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.workflow import (
    WorkflowResponse,
    WorkflowGenerateRequest,
    WorkflowGenerateResponse,
)
from app.services import nl_workflow_service
from app.repositories import workflow as workflow_repo
from app.core.logger import logger

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/generate", response_model=WorkflowGenerateResponse)
def generate_workflow(
    payload: WorkflowGenerateRequest,
    db: Session = Depends(get_db),
):
    try:
        result = nl_workflow_service.generate_workflow_service(
            user_request=payload.user_request,
            name=payload.name,
            domain=payload.domain,
            db=db,
        )
        return result
    except ValueError as e:
        logger.warning("route_generate_workflow_failed",
                       extra={"extra_data": {"error": str(e),
                                             "user_request": payload.user_request[:120],
                                             "domain": payload.domain}})
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error("route_generate_workflow_llm_error",
                     extra={"extra_data": {"error": str(e)}})
        raise HTTPException(status_code=502, detail="LLM generation failed")


@router.get("/", response_model=List[WorkflowResponse])
def list_workflows(domain: str | None = None, db: Session = Depends(get_db)):
    return workflow_repo.list_by_domain(db, domain)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    result = workflow_repo.get_by_id(db, workflow_id)
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result
