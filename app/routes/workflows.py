from fastapi import APIRouter, Depends, HTTPException, Header
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
from app.workflow.workflow_provenance import WorkflowProvenanceService
from app.workflow.publication_service import WorkflowPublicationService
from app.storage.service import FileStorageService
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
def list_workflows(
    domain: str | None = None,
    workspace_id: int | None = None,
    db: Session = Depends(get_db),
):
    return workflow_repo.list_workflows(db, domain=domain, workspace_id=workspace_id)


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


@router.get("/{workflow_id}/provenance")
def get_workflow_provenance(workflow_id: int, db: Session = Depends(get_db)):
    """Trace each workflow step back to its source (BRD clause + confidence).

    Derived on demand from the extraction mappings — no stored state.
    """
    result = WorkflowProvenanceService().for_workflow(db, workflow_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.post("/{workflow_id}/publish")
def publish_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    x_user_id: str | None = Header(default=None),
    x_workspace_id: str | None = Header(default=None),
):
    """Publish a workflow after passing three gates:
      1. Caller has workflow:publish permission
      2. All HumanTask steps have allowed_roles
      3. No unresolved rule conflicts in the workspace

    On success: status → published, skill.md generated.
    On failure: 422 with structured check results.
    """
    svc    = WorkflowPublicationService()
    result = svc.publish(workflow_id=workflow_id, user_id=x_user_id, db=db)

    if result.success:
        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": "Workflow published. Skill file generated.",
        }

    if result.error in ("workflow_not_found",):
        raise HTTPException(status_code=404, detail="Workflow not found")

    if result.error == "already_published":
        raise HTTPException(status_code=409, detail="Workflow is already published")

    # Gate failures → 422 with details
    raise HTTPException(
        status_code=422,
        detail={
            "message": "Publication blocked",
            "failed_checks": [
                {
                    "check":   c.check,
                    "detail":  c.detail,
                    "step_id": c.step_id,
                }
                for c in result.failed_checks
            ],
        },
    )


@router.get("/{workflow_id}/skill")
def get_skill_file(
    workflow_id: int,
    db: Session = Depends(get_db),
    x_user_id: str | None = Header(default=None),
    x_workspace_id: str | None = Header(default=None),
):
    """Return the skill.md guide for a published workflow.

    Requires workflow:read permission.
    Returns text/markdown content.
    """
    from fastapi.responses import Response
    from app.rbac.permission_checker import PermissionChecker

    workflow = workflow_repo.get_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow.status != "published":
        raise HTTPException(
            status_code=404,
            detail="Skill file not available — workflow is not published",
        )

    if not workflow.skill_file_path:
        raise HTTPException(
            status_code=404,
            detail="Skill file has not been generated for this workflow",
        )

    # RBAC check (soft — if no user header, skip; tighten when auth middleware added)
    if x_user_id and x_workspace_id:
        try:
            checker = PermissionChecker(db)
            ws_id   = int(x_workspace_id)
            if not checker.can(x_user_id, "workflow:read", ws_id):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        except ValueError:
            pass  # bad header value — let it through without auth

    try:
        storage  = FileStorageService()
        content  = storage.retrieve(workflow.skill_file_path)
        filename = f"skill-{workflow_id}.md"
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        logger.error("skill_file_retrieve_failed", extra={"extra_data": {
            "workflow_id": workflow_id, "error": str(exc),
        }})
        raise HTTPException(status_code=404, detail="Skill file could not be retrieved")
