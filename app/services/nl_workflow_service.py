"""
app/services/nl_workflow_service.py

Application-layer orchestrator for NL → workflow generation + save.

Responsibilities:
- Assemble NLPWorkflowService with all dependencies
- Run the NLP pipeline (returns compile_result)
- Hand compile_result to WorkflowPersistenceService to save
- Return structured HTTP response
"""

from sqlalchemy.orm import Session

from app.core.logger import logger

# NLP pipeline
from app.nlp.catalog.matcher import CatalogMatcher
from app.nlp.catalog.trigger_repository import TriggerDefinitionRepository
from app.nlp.catalog.action_repository import ActionDefinitionRepository
from app.nlp.suitability.suitability_agent import SuitabilityAgent
from app.prompting import PromptManager
from app.nlp.llm_manager.llm_manager import LLMManager
from app.nlp.services.nl_workflow_service import NLPWorkflowService

# Workflow compile + save
from app.workflow.workflow_generator import WorkflowGenerator
from app.workflow.workflow_response_parser import WorkflowResponseParser
from app.workflow.workflow_schema_validator import WorkflowSchemaValidator
from app.workflow.workflow_validator import WorkflowValidator
from app.workflow.workflow_repair_service import WorkflowRepairService
from app.workflow.workflow_compiler_service import WorkflowCompilerService
from app.workflow.workflow_persistence_service import WorkflowPersistenceService
from app.workflow.workflow_explainer import WorkflowExplainer
from app.dsl.dsl_generator import DSLGenerator
from app.nlp.parsers.rule_parser import RuleParser
from app.nlp.ast.builder import WorkflowASTBuilder
from app.nlp.ast.validator import ASTValidator
from app.nlp.complier.workflow_complier import WorkflowComplier
from app.semantic.semantic_catalog_retriever import SemanticCatalogRetriever
from app.core.domains import ALLOWED_DOMAINS

# Workspace-scoped generation
from app.nlp.catalog.workspace_catalog_matcher import WorkspaceCatalogMatcher
from app.workflow.workspace_context import build_workspace_prompt_vars
from app.models.workspace import Workspace
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workflow_actor import WorkflowActor
from app.models.workflow_business_rule import WorkflowBusinessRule

# Prompt template version used for workspace-scoped generation. The global path
# stays on the active version (v1) and is unaffected.
WORKSPACE_PROMPT_VERSION = "v2"


def _build_compiler_service() -> WorkflowCompilerService:
    return WorkflowCompilerService(
        dsl_generator=DSLGenerator(),
        rule_parser=RuleParser(),
        ast_builder=WorkflowASTBuilder(),
        ast_validator=ASTValidator(),
        workflow_compiler=WorkflowComplier(),
    )


def _build_nlp_service(db: Session) -> NLPWorkflowService:
    return NLPWorkflowService(
        catalog_matcher=CatalogMatcher(
            TriggerDefinitionRepository(db),
            ActionDefinitionRepository(db),
            SemanticCatalogRetriever(),
        ),
        suitability_agent=SuitabilityAgent(),
        prompt_manager=PromptManager(),
        workflow_generator=WorkflowGenerator(
            llm_manager=LLMManager(),
            response_parse=WorkflowResponseParser(),
        ),
        schema_validator=WorkflowSchemaValidator(),
        workflow_validator=WorkflowValidator(),
        workflow_repair_service=WorkflowRepairService(),
        compiler_service=_build_compiler_service(),
        db=db,
        domain=None,
    )


def generate_workflow_service(
    user_request: str,
    name: str,
    domain: str,
    db: Session,
    nlp_service: NLPWorkflowService | None = None,
    persistence_service: WorkflowPersistenceService | None = None,
) -> dict:
    """
    Full pipeline: NL → compile → save → return response.

    Raises:
        ValueError: invalid domain, suitability rejected, all retries failed
        RuntimeError: unrecoverable LLM failure
    """
    if domain not in ALLOWED_DOMAINS:
        raise ValueError(
            f"Invalid domain '{domain}'. Allowed: {sorted(ALLOWED_DOMAINS)}"
        )

    if nlp_service is None:
        nlp_service = _build_nlp_service(db)
    nlp_service._domain = domain

    logger.info("nl_workflow_generation_started",
                extra={"extra_data": {"user_request": user_request[:120], "domain": domain}})

    # NLP pipeline → returns compile_result: {dsl, ast, compiled}
    compile_result = nlp_service.generate(user_request)

    # Deterministic, catalog-grounded explanation of the generated workflow.
    explanation = None
    try:
        explanation = WorkflowExplainer().explain(
            compiled=compile_result.get("compiled", {}),
            db=db,
            domain=domain,
        )
    except Exception as exc:  # noqa: BLE001 - explanation is best-effort, never blocks generation
        logger.warning(
            "workflow_explanation_failed",
            extra={"extra_data": {"error": str(exc)}},
        )

    # Persist compiled result
    persistence = persistence_service or WorkflowPersistenceService()
    saved = persistence.save(
        db=db,
        name=name,
        domain=domain,
        user_request=user_request,
        compile_result=compile_result,
        explanation=explanation,
    )

    return {
        "workflow_id": saved["workflow_id"],
        "name": saved["name"],
        "domain": saved["domain"],
        "dsl": saved["dsl"],
        "execution_plan": {},
        "parsed_rule_json": saved["parsed_rule_json"],
        "explanation": saved.get("explanation"),
    }


# ── Workspace-scoped generation ───────────────────────────────────────────────

def _workspace_actors(db: Session, workspace_id: int) -> list[str]:
    rows = (
        db.query(WorkflowActor.name, WorkflowActor.role)
        .join(
            WorkflowKnowledge,
            WorkflowKnowledge.id == WorkflowActor.workflow_knowledge_id,
        )
        .filter(WorkflowKnowledge.workspace_id == workspace_id)
        .all()
    )
    labels: list[str] = []
    for name, role in rows:
        label = f"{name} ({role})" if role else name
        if label and label not in labels:
            labels.append(label)
    return labels


def _workspace_business_rules(db: Session, workspace_id: int) -> list[str]:
    rows = (
        db.query(WorkflowBusinessRule.rule)
        .join(
            WorkflowKnowledge,
            WorkflowKnowledge.id == WorkflowBusinessRule.workflow_knowledge_id,
        )
        .filter(WorkflowKnowledge.workspace_id == workspace_id)
        .all()
    )
    rules: list[str] = []
    for (rule,) in rows:
        if rule and rule not in rules:
            rules.append(rule)
    return rules


def generate_workspace_workflow_service(
    db: Session,
    workspace_id: int,
    name: str,
    user_request: str,
    domain: str,
    selected_action_ids: list[int] | None = None,
    nlp_service: NLPWorkflowService | None = None,
    persistence_service: WorkflowPersistenceService | None = None,
    progress_callback=None,
    budget_seconds: float | None = None,
) -> dict:
    """Workspace-scoped NL → workflow generation.

    Grounds the LLM ONLY in the workspace's mapped actions/triggers (+ any
    explicitly selected global actions) and the workspace's business rules —
    never the full global catalog.

    Args:
        progress_callback:  optional callable(event_name, data). Forwarded to
                            NLPWorkflowService.generate() and also called here
                            for compiled/step/explanation/saved/chains events.
                            When None the function runs synchronously as before.
        budget_seconds:     overall wall-clock budget for the LLM retry loop.
                            Defaults to GENERATION_BUDGET_SECONDS env var.

    Raises:
        ValueError: invalid domain, workspace has no mapped actions, suitability
                    rejected, or all generation attempts failed.
        RuntimeError: unrecoverable LLM failure.
    """
    from app.core.config import GENERATION_BUDGET_SECONDS
    budget = budget_seconds if budget_seconds is not None else GENERATION_BUDGET_SECONDS

    def _emit(event: str, data: dict) -> None:
        """Push a progress event. Never raises — transport errors must not block generation."""
        if progress_callback is not None:
            try:
                progress_callback(event, data)
            except Exception:  # noqa: BLE001
                pass

    if domain not in ALLOWED_DOMAINS:
        raise ValueError(
            f"Invalid domain '{domain}'. Allowed: {sorted(ALLOWED_DOMAINS)}"
        )

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if workspace is None:
        raise ValueError(f"Workspace {workspace_id} not found.")

    _emit("started", {
        "workspace_id":  workspace_id,
        "name":          name,
        "domain":        domain,
        "budget_seconds": budget,
    })

    # Workspace-scoped candidate set — the global catalog is never consulted.
    catalog_result = WorkspaceCatalogMatcher(db).match(
        workspace_id, user_request, selected_action_ids or []
    )
    if not catalog_result.action_names:
        raise ValueError(
            "Workspace has no mapped actions to generate from. Ingest BRDs whose "
            "actions resolve to the catalog, or add actions explicitly."
        )

    _emit("catalog_matched", {
        "action_count":  len(catalog_result.action_names),
        "trigger_count": len(catalog_result.trigger_names),
    })

    extra_variables = build_workspace_prompt_vars(
        display_name=workspace.display_name,
        description=workspace.description,
        actors=_workspace_actors(db, workspace_id),
        rules=_workspace_business_rules(db, workspace_id),
    )

    _emit("context_built", {
        "actor_count": len(extra_variables.get("workspace_summary", "").split(",")),
        "rule_count":  extra_variables.get("business_rules", "").count("\n") + 1,
    })

    if nlp_service is None:
        nlp_service = _build_nlp_service(db)
    nlp_service._domain = domain

    logger.info(
        "workspace_workflow_generation_started",
        extra={"extra_data": {
            "workspace_id":      workspace_id,
            "user_request":      user_request[:120],
            "domain":            domain,
            "candidate_actions": len(catalog_result.action_names),
        }},
    )

    # NLP pipeline — emits llm_started / llm_attempt_failed / llm_success
    # internally via the forwarded progress_callback
    compile_result = nlp_service.generate(
        user_request,
        catalog_result=catalog_result,
        extra_variables=extra_variables,
        prompt_version=WORKSPACE_PROMPT_VERSION,
        progress_callback=progress_callback,
        budget_seconds=budget,
    )

    # Emit compiled + individual step events so the UI can animate the DAG
    compiled = compile_result.get("compiled", {})
    _emit("compiled", {
        "step_count": len(compiled.get("steps", [])),
        "trigger":    compiled.get("trigger", {}).get("event_type", ""),
    })

    # Resolve action mappings once for enriched step events (rules + actors)
    from app.models.workflow_action_mapping import WorkflowActionMapping, MappingStatus
    from app.models.workflow_knowledge import WorkflowKnowledge as _WK
    action_meta: dict = {}
    try:
        rows = (
            db.query(WorkflowActionMapping)
            .join(_WK, _WK.id == WorkflowActionMapping.workflow_knowledge_id)
            .filter(
                _WK.workspace_id == workspace_id,
                WorkflowActionMapping.status == MappingStatus.MAPPED,
                WorkflowActionMapping.action_name.isnot(None),
            )
            .all()
        )
        action_meta = {
            r.action_name: {
                "display_name": r.display_name or r.action_name,
                "rules":        r.applicable_rules or [],
                "actors":       r.responsible_actors or [],
            }
            for r in rows
        }
    except Exception:  # noqa: BLE001
        pass

    for step in compiled.get("steps", []):
        action_name = step.get("action", "")
        meta = action_meta.get(action_name, {})
        _emit("step", {
            "id":           step.get("id"),
            "action":       action_name,
            "display_name": meta.get("display_name", action_name),
            "depends_on":   step.get("depends_on", []),
            "rules":        meta.get("rules", []),
            "actors":       meta.get("actors", []),
        })

    # Explanation — best-effort, never blocks
    explanation = None
    try:
        explanation = WorkflowExplainer().explain(
            compiled=compiled,
            db=db,
            domain=domain,
        )
        if explanation:
            _emit("explanation", {
                "summary": explanation.get("summary", ""),
                "trigger": explanation.get("trigger", {}),
                "steps":   explanation.get("steps", []),
            })
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "workspace_workflow_explanation_failed",
            extra={"extra_data": {"error": str(exc)}},
        )

    # Persist
    persistence = persistence_service or WorkflowPersistenceService()
    saved = persistence.save(
        db=db,
        name=name,
        domain=domain,
        user_request=user_request,
        compile_result=compile_result,
        explanation=explanation,
        workspace_id=workspace_id,
    )
    _emit("saved", {
        "workflow_id":  saved["workflow_id"],
        "name":         saved["name"],
        "workspace_id": workspace_id,
    })

    # Chain detection — separate session, never blocks the response
    try:
        from app.workflow.workflow_chain_detector import WorkflowChainDetector
        from app.db.session import SessionLocal
        chain_db = SessionLocal()
        try:
            chains = WorkflowChainDetector().detect(chain_db, workspace_id)
            chain_db.commit()
            if chains:
                _emit("chains_detected", {
                    "chains": [
                        {
                            "source_action":    c.source_action,
                            "target_workflow":  c.target_workflow_id,
                            "target_trigger":   c.target_trigger,
                            "confidence":       round(c.confidence, 2),
                            "match_type":       c.match_type,
                        }
                        for c in chains
                    ],
                })
        finally:
            chain_db.close()
    except Exception as chain_exc:  # noqa: BLE001
        logger.warning(
            "post_generation_chain_detection_failed",
            extra={"extra_data": {
                "workspace_id": workspace_id,
                "error":        str(chain_exc),
            }},
        )

    _emit("done", {
        "workflow_id": saved["workflow_id"],
    })

    return {
        "workflow_id":      saved["workflow_id"],
        "name":             saved["name"],
        "domain":           saved["domain"],
        "workspace_id":     workspace_id,
        "dsl":              saved["dsl"],
        "execution_plan":   {},
        "parsed_rule_json": saved["parsed_rule_json"],
        "explanation":      saved.get("explanation"),
    }
