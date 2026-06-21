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
from app.nlp.catalog.triggerRepository import TriggerDefinitionRepository
from app.nlp.catalog.actionRepository import ActionDefinitionRepository
from app.nlp.suitability.suitability_agent import SuitabilityAgent
from app.nlp.prompts.builder import PromptBuilder
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
from app.dsl.dsl_generator import DSLGenerator
from app.nlp.parsers.rule_parser import RuleParser
from app.nlp.ast.builder import WorkflowASTBuilder
from app.nlp.ast.validator import ASTValidator
from app.nlp.complier.workflow_complier import WorkflowComplier
from app.semantic.semantic_catalog_retriever import SemanticCatalogRetriever
ALLOWED_DOMAINS = {
    "finance",
    "health",
    "support",
}


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
        prompt_builder=PromptBuilder(),
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

    nlp_service = _build_nlp_service(db)
    nlp_service._domain = domain

    logger.info("nl_workflow_generation_started",
                extra={"extra_data": {"user_request": user_request[:120], "domain": domain}})

    # NLP pipeline → returns compile_result: {dsl, ast, compiled}
    compile_result = nlp_service.generate(user_request)

    # Persist compiled result
    persistence = WorkflowPersistenceService()
    saved = persistence.save(
        db=db,
        name=name,
        domain=domain,
        user_request=user_request,
        compile_result=compile_result,
    )

    return {
        "workflow_id": saved["workflow_id"],
        "name": saved["name"],
        "domain": saved["domain"],
        "dsl": saved["dsl"],
        "execution_plan": {},
        "parsed_rule_json": saved["parsed_rule_json"],
    }
