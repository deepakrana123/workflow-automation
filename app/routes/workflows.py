from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.workflow import (
    WorkflowResponse,
    WorkflowGenerateRequest,
    WorkflowGenerateResponse,
)
from app.services import workflow_service
from app.services import nl_workflow_service
from app.core.logger import logger

router = APIRouter(prefix="/workflows", tags=["workflows"])


# ── NL generation ─────────────────────────────────────────────────────────────

@router.post("/generate", response_model=WorkflowGenerateResponse)
def generate_workflow(
    payload: WorkflowGenerateRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a workflow from a natural language request.

    Runs the full pipeline:
      CatalogMatcher → SuitabilityAgent → PromptBuilder
      → LLM (with retry + fallback) → Validate → DSL → Save
    """
    try:
        result = nl_workflow_service.generate_workflow_service(
            user_request=payload.user_request,
            name=payload.name,
            domain=payload.domain,
            db=db,
        )
        return result
    except ValueError as e:
        logger.warning(
            "route_generate_workflow_failed",
            extra={
                "extra_data": {
                    "error": str(e),
                    "user_request": payload.user_request[:120],
                    "domain": payload.domain,
                }
            },
        )
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(
            "route_generate_workflow_llm_error",
            extra={"extra_data": {"error": str(e)}},
        )
        raise HTTPException(status_code=502, detail="LLM generation failed")


# ── Workflow read ──────────────────────────────────────────────────────────────

@router.get("/", response_model=List[WorkflowResponse])
def list_workflows(domain: str | None = None, db: Session = Depends(get_db)):
    return workflow_service.list_workflow_service(domain, db)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    try:
        return workflow_service.get_workflow_service(workflow_id, db)
    except ValueError as e:
        logger.warning(
            "route_get_workflow_not_found",
            extra={"extra_data": {"workflow_id": workflow_id}},
        )
        raise HTTPException(status_code=404, detail=str(e))
