"""
app/routes/workspaces.py

Workspace-level endpoints.

Currently exposes the multi-BRD knowledge synthesis (aggregated, deduplicated,
provenance-rich view across all BRDs in a workspace). Workspace CRUD will live
here too.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
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
from app.workflow.workflow_chain_detector import WorkflowChainDetector
from app.workflow.workflow_merge_suggestion import WorkflowMergeSuggestionService
from app.models.workflow_chain import WorkflowChain, ChainStatus
from app.models.workflow import Workflow

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


class GenerateBRDWorkflowRequest(BaseModel):
    name: str
    user_request: str
    domain: str = "finance"


@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(active_only: bool = True, db: Session = Depends(get_db)):
    """List workspaces (active by default)."""
    query = db.query(Workspace)
    if active_only:
        query = query.filter(Workspace.active.is_(True))
    return query.order_by(Workspace.id.asc()).all()


@router.post("", response_model=WorkspaceResponse, status_code=201)
def create_workspace(body: WorkspaceCreate, db: Session = Depends(get_db)):
    """Create a workspace at a specific level in the bank hierarchy.

    Rules:
      - global   → parent_id must be None
      - region   → parent_id must point to a global workspace
      - zone     → parent_id must point to a region workspace
      - branch   → parent_id must point to a zone workspace
    """
    from app.models.workspace import WORKSPACE_LEVELS, _PARENT_LEVEL

    # Parent validation skipped for now — level defaults to branch,
    # hierarchy enforcement will be added when multi-level rule inheritance
    # is required.
    if body.parent_id is not None:
        parent = db.query(Workspace).filter(Workspace.id == body.parent_id).first()
        if parent is None:
            raise HTTPException(
                status_code=404,
                detail=f"Parent workspace {body.parent_id} not found.",
            )

    # Enforce single global workspace per deployment
    if body.level == "global":
        existing_global = (
            db.query(Workspace).filter(Workspace.level == "global").first()
        )
        if existing_global is not None:
            raise HTTPException(
                status_code=409,
                detail=f"A global workspace already exists (id={existing_global.id}). "
                       "Only one global workspace is allowed per deployment.",
            )

    workspace = Workspace(
        name=body.name,
        display_name=body.display_name,
        description=body.description,
        organization_name=body.organization_name,
        level=body.level,
        parent_id=body.parent_id,
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


@router.post("/{workspace_id}/brds/{brd_id}/generate")
def generate_brd_workflow(
    workspace_id: int,
    brd_id: int,
    body: GenerateBRDWorkflowRequest,
    db: Session = Depends(get_db),
):
    """Generate a workflow grounded in a single BRD.

    Restricts the candidate action/trigger set to the specified
    workflow_knowledge_id (brd_id) only — actions from other BRDs in the
    workspace are excluded. This produces a workflow that faithfully reflects
    one BRD rather than a blend of all BRDs.

    When the workspace has more than one BRD, call
    POST /workspaces/{id}/synthesize afterward (or let the auto-merge run)
    to combine per-BRD workflows into one end-to-end workflow.
    """
    _require_workspace(db, workspace_id)

    # Verify the BRD exists and belongs to this workspace
    from app.models.workflow_knowledge import WorkflowKnowledge
    brd = db.query(WorkflowKnowledge).filter(
        WorkflowKnowledge.id == brd_id,
        WorkflowKnowledge.workspace_id == workspace_id,
    ).first()
    if brd is None:
        raise HTTPException(status_code=404, detail="BRD not found in this workspace.")

    try:
        return nl_workflow_service.generate_workspace_workflow_service(
            db=db,
            workspace_id=workspace_id,
            name=body.name,
            user_request=body.user_request,
            domain=body.domain,
            brd_id=brd_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError:
        raise HTTPException(status_code=502, detail="LLM generation failed")


@router.post("/{workspace_id}/generate/stream")
async def generate_workspace_workflow_stream(
    workspace_id: int,
    body: GenerateWorkflowRequest,
    db: Session = Depends(get_db),
):
    """
    Stream workspace workflow generation progress as Server-Sent Events.

    The client connects via fetch() + ReadableStream (not EventSource — POST
    with a JSON body is required for auth and structured params).

    Events emitted in order:
      started, catalog_matched, context_built,
      llm_started, llm_attempt_failed*, llm_success,
      compiled, step (one per DAG step), explanation,
      saved, chains_detected*, done

    On any failure:
      error event with {code, message, retryable}

    The blocking POST /{workspace_id}/generate remains unchanged and unaffected.
    """
    from app.services.generation_stream_service import WorkspaceGenerationStreamService
    _require_workspace(db, workspace_id)

    svc = WorkspaceGenerationStreamService()
    return StreamingResponse(
        svc.stream(
            db=db,
            workspace_id=workspace_id,
            name=body.name,
            user_request=body.user_request,
            domain=body.domain,
            selected_action_ids=body.selected_action_ids,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",    # disable nginx buffering
            "Connection":        "keep-alive",
        },
    )


# ── Chain request/response models ─────────────────────────────────────────────

class ChainPatchRequest(BaseModel):
    status: str          # accepted | rejected
    note: str | None = None


class SuggestMergeRequest(BaseModel):
    workflow_ids: list[int]


class AcceptMergeRequest(BaseModel):
    merged_name: str
    domain: str = "finance"
    steps: list[dict]                      # list of {action, source_workflow, depends_on, note}
    workflow_label_map: dict[str, int] = {}  # {"A": workflow_id, "B": workflow_id, ...}


# ── Chain detection endpoints ──────────────────────────────────────────────────

@router.post("/{workspace_id}/detect-chains")
def detect_chains(workspace_id: int, db: Session = Depends(get_db)):
    """
    Detect sequential and conditional connections between workflows in this workspace.

    Runs three detection passes:
      1. name_match   — terminal action name matches target trigger exactly (auto-accepted)
      2. fts_match    — full-text similarity above threshold (suggested)
      3. rule_mention — applicable_rule text mentions another workflow's trigger (suggested)

    Idempotent — safe to call after every workflow generation. Stale auto/suggested
    chains are replaced; accepted/rejected user decisions are preserved.
    """
    _require_workspace(db, workspace_id)
    try:
        chains = WorkflowChainDetector().detect(db, workspace_id)
        db.commit()
        return {
            "workspace_id": workspace_id,
            "chains_detected": len(chains),
            "chains": [_serialize_chain(c) for c in chains],
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{workspace_id}/chains")
def list_chains(
    workspace_id: int,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """
    List detected workflow chains for this workspace.

    Optional ?status= filter: suggested | accepted | rejected | auto
    """
    _require_workspace(db, workspace_id)
    q = db.query(WorkflowChain).filter(
        WorkflowChain.workspace_id == workspace_id
    )
    if status:
        q = q.filter(WorkflowChain.status == status)
    chains = q.order_by(WorkflowChain.confidence.desc()).all()
    return [_serialize_chain(c) for c in chains]


@router.patch("/{workspace_id}/chains/{chain_id}")
def update_chain(
    workspace_id: int,
    chain_id: int,
    body: ChainPatchRequest,
    db: Session = Depends(get_db),
):
    """
    Accept or reject a detected chain suggestion.

    On accept:
      - Sets chain status to accepted
      - Writes on_success_dispatch into the source workflow's terminal step config
        so the DAG executor fires the target workflow on step completion

    On reject:
      - Sets chain status to rejected (never overwritten by future detection runs)
    """
    _require_workspace(db, workspace_id)

    if body.status not in ("accepted", "rejected"):
        raise HTTPException(
            status_code=400,
            detail="status must be 'accepted' or 'rejected'",
        )

    chain = db.query(WorkflowChain).filter(
        WorkflowChain.id == chain_id,
        WorkflowChain.workspace_id == workspace_id,
    ).first()

    if chain is None:
        raise HTTPException(status_code=404, detail="Chain not found.")

    chain.status = body.status
    if body.note:
        chain.note = body.note

    if body.status == "accepted":
        _write_dispatch_to_dag(db, chain)

    db.commit()
    return _serialize_chain(chain)


# ── Merge suggestion endpoints ─────────────────────────────────────────────────

@router.post("/{workspace_id}/suggest-merge")
def suggest_merge(
    workspace_id: int,
    body: SuggestMergeRequest,
    db: Session = Depends(get_db),
):
    """
    Ask the LLM to suggest how 2–3 workflows could be merged into one.

    Returns a suggestion dict — nothing is persisted. The user reviews and
    optionally accepts via /accept-merge.
    """
    _require_workspace(db, workspace_id)

    if len(body.workflow_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 workflow_ids required.")
    if len(body.workflow_ids) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 workflow_ids per merge suggestion.")

    try:
        suggestion = WorkflowMergeSuggestionService().suggest(
            db=db,
            workspace_id=workspace_id,
            workflow_ids=body.workflow_ids,
        )
        return suggestion
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError:
        raise HTTPException(status_code=502, detail="LLM merge suggestion failed")


@router.post("/{workspace_id}/accept-merge")
def accept_merge(
    workspace_id: int,
    body: AcceptMergeRequest,
    db: Session = Depends(get_db),
):
    """
    Compile and persist a merge suggestion as a new workflow.

    The steps list from suggest-merge is compiled through WorkflowCompilerService
    and saved as a new Workflow row in this workspace.
    """
    from app.workflow.workflow_compiler_service import WorkflowCompilerService
    from app.workflow.workflow_persistence_service import WorkflowPersistenceService
    from app.dsl.dsl_generator import DSLGenerator
    from app.nlp.parsers.rule_parser import RuleParser
    from app.nlp.ast.builder import WorkflowASTBuilder
    from app.nlp.ast.validator import ASTValidator
    from app.nlp.complier.workflow_complier import WorkflowComplier

    _require_workspace(db, workspace_id)

    if not body.steps:
        raise HTTPException(status_code=400, detail="steps list is required.")

    # Resolve the trigger from the first step's source workflow using the
    # label map ({"A": workflow_id}) passed back from suggest-merge.
    # This is more reliable than matching by workflow name.
    trigger_name = "merged_workflow_triggered"
    first_step = body.steps[0] if body.steps else {}
    source_label = first_step.get("source_workflow", "")
    source_wf_id = body.workflow_label_map.get(source_label) if body.workflow_label_map else None

    if source_wf_id:
        source_wf = db.query(Workflow).filter(
            Workflow.id == source_wf_id,
            Workflow.workspace_id == workspace_id,
        ).first()
        if source_wf and source_wf.parsed_rule_json:
            t = source_wf.parsed_rule_json.get("trigger", {})
            trigger_name = t.get("event_type", trigger_name)

    workflow_json = {
        "workflow": {
            "triggers": [{"name": trigger_name}],
            "actions": [
                {
                    "name": step["action"],
                    "dependencies": step.get("depends_on") or [],
                }
                for step in body.steps
            ],
        }
    }

    try:
        compiler = WorkflowCompilerService(
            dsl_generator=DSLGenerator(),
            rule_parser=RuleParser(),
            ast_builder=WorkflowASTBuilder(),
            ast_validator=ASTValidator(),
            workflow_compiler=WorkflowComplier(),
        )
        compile_result = compiler.compile(body.domain, workflow_json)

        saved = WorkflowPersistenceService().save(
            db=db,
            name=body.merged_name,
            domain=body.domain,
            user_request=f"Merged workflow: {body.merged_name}",
            compile_result=compile_result,
            workspace_id=workspace_id,
        )

        # Auto-run chain detection for the new merged workflow
        try:
            from app.db.session import SessionLocal
            chain_db = SessionLocal()
            try:
                WorkflowChainDetector().detect(chain_db, workspace_id)
                chain_db.commit()
            finally:
                chain_db.close()
        except Exception:
            pass  # chain detection failure never blocks the merge persist

        return saved

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ── Private serializers ────────────────────────────────────────────────────────

def _serialize_chain(chain: WorkflowChain) -> dict:
    return {
        "id":                 chain.id,
        "workspace_id":       chain.workspace_id,
        "source_workflow_id": chain.source_workflow_id,
        "source_step_id":     chain.source_step_id,
        "source_action":      chain.source_action,
        "target_workflow_id": chain.target_workflow_id,
        "target_trigger":     chain.target_trigger,
        "match_type":         chain.match_type,
        "confidence":         chain.confidence,
        "status":             chain.status,
        "note":               chain.note,
        "detected_at":        chain.detected_at.isoformat() if chain.detected_at else None,
    }


def _write_dispatch_to_dag(db: Session, chain: WorkflowChain) -> None:
    """
    Write on_success_dispatch into the source workflow's terminal step config.

    Mutates parsed_rule_json in place — the step whose id == chain.source_step_id
    gets config.on_success_dispatch = {"workflow_id": chain.target_workflow_id}.
    """
    source_wf = db.query(Workflow).filter(
        Workflow.id == chain.source_workflow_id
    ).first()
    if not source_wf or not source_wf.parsed_rule_json:
        return

    import copy
    dag = copy.deepcopy(source_wf.parsed_rule_json)
    updated = False

    for step in dag.get("steps", []):
        if str(step["id"]) == str(chain.source_step_id):
            config = step.get("config") or {}
            config["on_success_dispatch"] = {"workflow_id": chain.target_workflow_id}
            step["config"] = config
            updated = True
            break

    if updated:
        source_wf.parsed_rule_json = dag
        db.flush()


# ── Unmapped action resolution endpoints ──────────────────────────────────────

class ResolveActionRequest(BaseModel):
    """
    Manual resolution for an unmapped BRD action.

    Mode A — map to existing catalog entry:
      Provide action_definition_id. All snapshot fields are copied automatically
      from the ActionDefinition. No other fields needed.

    Mode B — custom resolution:
      Leave action_definition_id null. Provide action_name (required) plus any
      other fields you want to set. The action becomes available for generation
      using action_name as the handler key.

    Fields:
      action_definition_id   optional int  — ID of an existing ActionDefinition
      action_name            optional str  — catalog name or custom handler name
      display_name           optional str  — human-readable label
      catalog_description    optional str  — what this action does
      aliases                optional list — alternative names for FTS matching
      workflow_type          optional str  — domain (e.g. "finance")
      input_schema           optional dict — input payload contract
      output_schema          optional dict — output payload contract
      execution_template     optional dict — {"execution_type": "python",
                                              "configuration": {"handler": "..."}}
    """
    action_definition_id: int | None = None
    action_name:          str | None = None
    display_name:         str | None = None
    catalog_description:  str | None = None
    aliases:              list[str] | None = None
    workflow_type:        str | None = None
    input_schema:         dict | None = None
    output_schema:        dict | None = None
    execution_template:   dict | None = None


@router.get("/{workspace_id}/unmapped-actions")
def list_unmapped_actions(
    workspace_id: int,
    db: Session = Depends(get_db),
):
    """
    List all BRD actions that the automatic mapper could not resolve.

    Each row includes:
      - extract_name: what the BRD called this action
      - description: BRD description of the action
      - query_text: what was sent to the retrieval pipeline
      - top_candidates: closest catalog matches that were rejected (with scores)
      - source_document: which BRD this came from

    Use GET /workspaces/{id}/unmapped-actions/{mapping_id}/suggestions to get
    fresh catalog match suggestions for a specific unmapped action.

    Use PATCH /workspaces/{id}/unmapped-actions/{mapping_id} to resolve one.
    """
    from app.services.unmapped_action_service import UnmappedActionService
    _require_workspace(db, workspace_id)
    svc = UnmappedActionService(db)
    return {
        "workspace_id":    workspace_id,
        "unmapped_actions": svc.list_unmapped(workspace_id),
    }


@router.get("/{workspace_id}/unmapped-actions/{mapping_id}/suggestions")
def get_action_suggestions(
    workspace_id: int,
    mapping_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """
    Get fresh catalog match suggestions for one unmapped action.

    Re-runs FTS search (websearch_to_tsquery) over ActionDefinition using the
    action's extract_name + description as the query. Returns up to `limit`
    candidates ordered by relevance score.

    Use the returned action_definition_id to resolve via PATCH.
    """
    from app.services.unmapped_action_service import UnmappedActionService
    _require_workspace(db, workspace_id)
    svc = UnmappedActionService(db)
    try:
        return {
            "mapping_id":  mapping_id,
            "suggestions": svc.suggest_catalog_matches(mapping_id, workspace_id, limit),
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/{workspace_id}/unmapped-actions/{mapping_id}")
def resolve_unmapped_action(
    workspace_id: int,
    mapping_id: int,
    body: ResolveActionRequest,
    db: Session = Depends(get_db),
):
    """
    Manually resolve an unmapped BRD action.

    Mode A — map to catalog:
      {"action_definition_id": 1618}
      Copies all fields from the ActionDefinition automatically.

    Mode B — custom values:
      {
        "action_name": "verify_property_title",
        "display_name": "Verify Property Title",
        "execution_template": {
          "execution_type": "python",
          "configuration": {"handler": "verify_property_title"}
        }
      }

    After resolution:
      - status becomes MAPPED
      - action becomes available in WorkspaceCatalogMatcher for generation
      - action becomes available in config_resolver for runtime execution
    """
    from app.services.unmapped_action_service import UnmappedActionService
    _require_workspace(db, workspace_id)
    svc = UnmappedActionService(db)
    try:
        return svc.resolve(
            mapping_id=mapping_id,
            workspace_id=workspace_id,
            action_definition_id=body.action_definition_id,
            action_name=body.action_name,
            display_name=body.display_name,
            catalog_description=body.catalog_description,
            aliases=body.aliases,
            workflow_type=body.workflow_type,
            input_schema=body.input_schema,
            output_schema=body.output_schema,
            execution_template=body.execution_template,
        )
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc))
