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
) -> dict:
    """Workspace-scoped NL → workflow generation.

    Grounds the LLM ONLY in the workspace's mapped actions/triggers (+ any
    explicitly selected global actions) and the workspace's business rules —
    never the full global catalog.

    Raises:
        ValueError: invalid domain, workspace has no mapped actions, suitability
                    rejected, or all generation attempts failed.
        RuntimeError: unrecoverable LLM failure.
    """
    if domain not in ALLOWED_DOMAINS:
        raise ValueError(
            f"Invalid domain '{domain}'. Allowed: {sorted(ALLOWED_DOMAINS)}"
        )

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if workspace is None:
        raise ValueError(f"Workspace {workspace_id} not found.")

    # Workspace-scoped candidate set — the global catalog is never consulted.
    catalog_result = WorkspaceCatalogMatcher(db).match(
        workspace_id, selected_action_ids or []
    )
    if not catalog_result.action_names:
        raise ValueError(
            "Workspace has no mapped actions to generate from. Ingest BRDs whose "
            "actions resolve to the catalog, or add actions explicitly."
        )

    extra_variables = build_workspace_prompt_vars(
        display_name=workspace.display_name,
        description=workspace.description,
        actors=_workspace_actors(db, workspace_id),
        rules=_workspace_business_rules(db, workspace_id),
    )

    if nlp_service is None:
        nlp_service = _build_nlp_service(db)
    nlp_service._domain = domain

    logger.info(
        "workspace_workflow_generation_started",
        extra={"extra_data": {
            "workspace_id": workspace_id,
            "user_request": user_request[:120],
            "domain": domain,
            "candidate_actions": len(catalog_result.action_names),
        }},
    )

    compile_result = nlp_service.generate(
        user_request,
        catalog_result=catalog_result,
        extra_variables=extra_variables,
        prompt_version=WORKSPACE_PROMPT_VERSION,
    )

    explanation = None
    try:
        explanation = WorkflowExplainer().explain(
            compiled=compile_result.get("compiled", {}),
            db=db,
            domain=domain,
        )
    except Exception as exc:  # noqa: BLE001 - explanation is best-effort
        logger.warning(
            "workspace_workflow_explanation_failed",
            extra={"extra_data": {"error": str(exc)}},
        )

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

    return {
        "workflow_id": saved["workflow_id"],
        "name": saved["name"],
        "domain": saved["domain"],
        "workspace_id": workspace_id,
        "dsl": saved["dsl"],
        "execution_plan": {},
        "parsed_rule_json": saved["parsed_rule_json"],
        "explanation": saved.get("explanation"),
    }
