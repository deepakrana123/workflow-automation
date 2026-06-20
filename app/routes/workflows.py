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


# ── Sub-resource endpoints for frontend workflow details page ──────────────────

@router.get("/{workflow_id}/dsl")
def get_workflow_dsl(workflow_id: int, db: Session = Depends(get_db)):
    """Return the DSL string from the compiled workflow stored in parsed_rule_json."""
    workflow = workflow_repo.get_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    parsed = workflow.parsed_rule_json or {}
    steps = parsed.get("steps", [])
    trigger = parsed.get("trigger", {})
    trigger_event = trigger.get("event_type", "unknown")

    # Rebuild DSL string from steps
    lines = []
    for step in steps:
        step_id = step.get("id", "?")
        action = step.get("action", "unknown")
        deps = step.get("depends_on", [])
        if deps:
            dep_str = ",".join(f"@{d}" for d in deps)
            lines.append(f"@{step_id} @depends({dep_str}): {trigger_event} -> {action}")
        else:
            lines.append(f"@{step_id}: {trigger_event} -> {action}")

    return {
        "dsl": "\n".join(lines),
        "workflow_id": workflow_id,
        "raw_input": workflow.raw_input,
    }


@router.get("/{workflow_id}/ast")
def get_workflow_ast(workflow_id: int, db: Session = Depends(get_db)):
    """Return AST-like representation built from parsed_rule_json."""
    workflow = workflow_repo.get_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    parsed = workflow.parsed_rule_json or {}
    steps = parsed.get("steps", [])
    trigger = parsed.get("trigger", {})

    nodes = [{"id": "trigger", "type": "trigger", "name": trigger.get("event_type", "unknown"), "config": {}}]
    edges = []

    for step in steps:
        step_id = str(step.get("id", ""))
        nodes.append({
            "id": step_id,
            "type": "action",
            "name": step.get("action", ""),
            "config": step.get("config", {}),
        })
        deps = step.get("depends_on", [])
        if not deps:
            edges.append({"source": "trigger", "target": step_id})
        for dep in deps:
            edges.append({"source": str(dep), "target": step_id})

    return {"type": "workflow_ast", "nodes": nodes, "edges": edges}


@router.get("/{workflow_id}/compiled")
def get_workflow_compiled(workflow_id: int, db: Session = Depends(get_db)):
    """Return the full parsed_rule_json (compiled DAG) as stored in DB."""
    workflow = workflow_repo.get_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.parsed_rule_json or {}
