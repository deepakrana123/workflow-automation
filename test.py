from app.db.session import SessionLocal

from app.nlp.catalog.triggerRepository import TriggerDefinitionRepository
from app.nlp.catalog.actionRepository import ActionDefinitionRepository

from app.nlp.catalog.matcher import CatalogMatcher

from app.nlp.domain.domain_detector import DomainDetector
from app.nlp.suitability.suitability_agent import SuitabilityAgent
from app.nlp.prompts.builder import PromptBuilder

from app.nlp.services.nl_workflow_service import NLPWorkflowService
from app.workflow.workflow_generator import WorkflowGenerator
from app.nlp.llm_manager.llm_manager import LLMManager
from app.workflow.workflow_schema_validator import WorkflowSchemaValidator
from app.workflow.workflow_validator import WorkflowValidator
from app.workflow.execution_plan_builder import ExecutionPlanBuilder
from app.workflow.workflow_repair_service import WorkflowRepairService
from app.dsl.dsl_validator import DSLValidator
from app.workflow.workflow_response_parser import WorkflowResponseParser
from app.dsl.dsl_generator import DSLGenerator

TEST_CASES = [
    "When payment due send reminder",
    "When payment missed escalate case and notify manager",
    "If fraud detected lock account and flag for review",
    "When complaint created notify customer",
    "When ticket created assign support agent",
    "When SLA breached notify manager",
    "When patient discharged send discharge instructions",
    "When appointment missed send medication reminder",
]


def main():

    db = SessionLocal()

    try:
        # context = PromptContext(
        #     workflow_type="finance",
        #     triggers=["payment_due"],
        #     actions=["send_reminder"],
        #     user_request="when payment due send reminder",
        # )
        # service = PromptService()
        # prompt = service.build(context)
        # print(prompt)

        trigger_repo = TriggerDefinitionRepository(db)
        action_repo = ActionDefinitionRepository(db)

        matcher = CatalogMatcher(
            trigger_repo,
            action_repo,
        )
        
        detector = DomainDetector()
        suitability = SuitabilityAgent()
        builder = PromptBuilder()
        llm_manager = LLMManager()
        workflow_response_parser = WorkflowResponseParser()
        workflow = WorkflowGenerator(llm_manager, workflow_response_parser)
        workflowschemaValidator = WorkflowSchemaValidator()
        dsl_validator = DSLValidator()
        workflowvalidator = WorkflowValidator()
        execution_plan_builder = ExecutionPlanBuilder()
        dsl_generator = DSLGenerator()
        workflow_repair_service = WorkflowRepairService()

        service = NLPWorkflowService(
            catalog_matcher=matcher,
            domain_detector=detector,
            suitability_agent=suitability,
            prompt_builder=builder,
            workflow_generator=workflow,
            schema_validator=workflowschemaValidator,
            dsl_validator=dsl_validator,
            workflowvalidator=workflowvalidator,
            execution_plan_builder=execution_plan_builder,
            dsl_generator=dsl_generator,
            workflow_repair_service=workflow_repair_service,
        )

        for case in TEST_CASES:

            print("=" * 80)
            print(case)

            result = service.generate(case)

            print(result)

    finally:
        db.close()


if __name__ == "__main__":
    main()
