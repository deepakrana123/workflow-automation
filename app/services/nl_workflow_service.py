"""
app/services/nl_workflow_service.py

Application-layer service for the NL workflow generation route.

Responsibilities:
- Validate domain
- Assemble NLPWorkflowService with all dependencies
- Run generation pipeline
- Persist result to DB
- Return structured response

NLPWorkflowService (app/nlp/services/) owns the pipeline logic.
This file owns the DB transaction and HTTP-layer contract.
"""

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.repositories import workflow as workflow_repo
from app.parsers.dag_orchestrator import parse_dag_workflow

# NLP pipeline dependencies
from app.nlp.catalog.matcher import CatalogMatcher
from app.nlp.catalog.triggerRepository import TriggerDefinitionRepository
from app.nlp.catalog.actionRepository import ActionDefinitionRepository
from app.nlp.domain.domain_detector import DomainDetector
from app.nlp.suitability.suitability_agent import SuitabilityAgent
from app.nlp.prompts.builder import PromptBuilder
from app.nlp.llm_manager.llm_manager import LLMManager
from app.nlp.services.nl_workflow_service import NLPWorkflowService

from app.workflow.workflow_generator import WorkflowGenerator
from app.workflow.workflow_response_parser import WorkflowResponseParser
from app.workflow.workflow_schema_validator import WorkflowSchemaValidator
from app.workflow.workflow_validator import WorkflowValidator
from app.workflow.execution_plan_builder import ExecutionPlanBuilder
from app.workflow.workflow_repair_service import WorkflowRepairService
from app.dsl.dsl_validator import DSLValidator
from app.dsl.dsl_generator import DSLGenerator


ALLOWED_DOMAINS = {
    "support",
    "health",
    "loan",
    "payments",
    "hr",
    "logistics",
    "ecommerce",
}


def _build_nlp_service(db: Session) -> NLPWorkflowService:
    """
    Assemble NLPWorkflowService with all dependencies.
    DB-scoped — trigger/action repos need the session.
    """
    trigger_repo = TriggerDefinitionRepository(db)
    action_repo = ActionDefinitionRepository(db)

    return NLPWorkflowService(
        catalog_matcher=CatalogMatcher(trigger_repo, action_repo),
        domain_detector=DomainDetector(),
        suitability_agent=SuitabilityAgent(),
        prompt_builder=PromptBuilder(),
        workflow_generator=WorkflowGenerator(
            llm_manager=LLMManager(),
            response_parse=WorkflowResponseParser(),
        ),
        execution_plan_builder=ExecutionPlanBuilder(),
        workflowvalidator=WorkflowValidator(),
        dsl_validator=DSLValidator(),
        schema_validator=WorkflowSchemaValidator(),
        dsl_generator=DSLGenerator(),
        workflow_repair_service=WorkflowRepairService(),
        db=db,
        domain=None,   # set per-call below
    )


def generate_workflow_service(
    user_request: str,
    name: str,
    domain: str,
    db: Session,
) -> dict:
    """
    Full NL → workflow pipeline.

    1. Validate domain
    2. Run NLPWorkflowService.generate()
    3. Parse DSL through dag_orchestrator for parsed_rule_json
    4. Persist to DB
    5. Return structured result

    Raises:
        ValueError: domain invalid, suitability rejected, all retries failed
        RuntimeError: unrecoverable LLM failure
    """
    if domain not in ALLOWED_DOMAINS:
        logger.warning(
            "nl_workflow_invalid_domain",
            extra={"extra_data": {"domain": domain}},
        )
        raise ValueError(f"Invalid domain '{domain}'. "
                         f"Allowed: {sorted(ALLOWED_DOMAINS)}")

    nlp_service = _build_nlp_service(db)
    nlp_service._domain = domain

    logger.info(
        "nl_workflow_generation_started",
        extra={"extra_data": {"user_request": user_request[:120], "domain": domain}},
    )

    # Run the full NL → validate → repair → DSL pipeline
    result = nlp_service.generate(user_request)

    dsl: str = result["dsl"]
    execution_plan: dict = result["execution_plan"]
    workflow_data: dict = result["workflow"]

    # Parse DSL through dag_orchestrator to get the canonical parsed_rule_json
    # that the runtime expects (v2 step format)
    dag_result = parse_dag_workflow(dsl)

    if not dag_result["validation"]["is_valid"]:
        logger.error(
            "nl_workflow_dsl_runtime_parse_failed",
            extra={
                "extra_data": {
                    "errors": dag_result["validation"]["errors"],
                    "dsl": dsl[:200],
                }
            },
        )
        raise ValueError(
            f"Generated DSL failed runtime validation: "
            f"{dag_result['validation']['errors']}"
        )

    parsed_rule_json = {
        "version": "v2",
        "steps": dag_result["steps"],
    }

    saved = workflow_repo.create(
        db=db,
        name=name,
        domain=domain,
        raw_input=user_request,
        parsed_rule_json=parsed_rule_json,
    )
    db.commit()
    db.refresh(saved)

    logger.info(
        "nl_workflow_created",
        extra={
            "extra_data": {
                "workflow_id": saved.id,
                "name": saved.name,
                "domain": saved.domain,
                "step_count": len(dag_result["steps"]),
            }
        },
    )

    return {
        "workflow_id": saved.id,
        "name": saved.name,
        "domain": saved.domain,
        "dsl": dsl,
        "execution_plan": execution_plan,
        "parsed_rule_json": parsed_rule_json,
    }
