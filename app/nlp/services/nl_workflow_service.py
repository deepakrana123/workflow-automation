from app.nlp.catalog.matcher import CatalogMatcher
from app.nlp.domain.domain_detector import DomainDetector
from app.nlp.suitability.suitability_agent import SuitabilityAgent
from app.nlp.prompts.builder import PromptBuilder
from app.nlp.prompts.prompt_context import PromptContext
from app.workflow.workflow_generator import WorkflowGenerator
from app.nlp.llm_manager.llm_manager import LLMManager
from app.workflow.workflow_schema_validator import WorkflowSchemaValidator
from app.workflow.workflow_validator import WorkflowValidator
from app.workflow.execution_plan_builder import ExecutionPlanBuilder
from app.dsl.dsl_validator import DSLValidator


class NLPWorkflowService:

    def __init__(
        self,
        catalog_matcher: CatalogMatcher,
        domain_detector: DomainDetector,
        suitability_agent: SuitabilityAgent,
        prompt_builder: PromptBuilder,
        workflow_generator: WorkflowGenerator,
        execution_plan_builder: ExecutionPlanBuilder,
        workflowvalidator: WorkflowValidator,
        dsl_validator: DSLValidator,
        schema_validator: WorkflowSchemaValidator,
    ):
        self.catalog_matcher = catalog_matcher
        self.domain_detector = domain_detector
        self.suitability_agent = suitability_agent
        self.prompt_builder = prompt_builder
        self.workflow_generator = workflow_generator
        self.workflowvalidator = workflowvalidator
        self.dsl_validator = dsl_validator
        self.execution_plan_builder = execution_plan_builder
        self.schema_validator = schema_validator

    def generate(
        self,
        user_request: str,
    ):
        catalog_result = self.catalog_matcher.match(user_request)

        # workflow_type = self.domain_detector.detect(
        #     catalog_result.matched_triggers,
        #     catalog_result.matched_actions,
        # )
        workflow_type = catalog_result.workflow_type

        suitability = self.suitability_agent.evaluate(
            workflow_type,
            catalog_result.trigger_names,
            catalog_result.action_names,
        )

        if not suitability.supported:
            raise ValueError(suitability.reason)

        context = PromptContext(
            workflow_type=workflow_type,
            triggers=[t.name for t in catalog_result.matched_triggers],
            actions=[a.name for a in catalog_result.matched_actions],
            user_request=user_request,
        )

        prompt = self.prompt_builder.build(context)

        result = self.workflow_generator.generate(prompt)
        workflow = result["workflow"]
        schema_result = self.schema_validator.validate(workflow)

        if not schema_result.valid:
            raise ValueError(schema_result.errors)
        workflow_result = self.workflow_validator.validat(workflow)

        if not workflow_result.valid:
            raise ValueError(workflow_result.errors)

        dsl = self.dsl_generator.generate(workflow_type, workflow)
        dsl_result = self.dsl_validator.validate(dsl)

        if not dsl_result["valid"]:
            raise ValueError(dsl_result["errors"])

        execution_plan = self.execution_plan_builder.build(workflow)
        return {"workflow": workflow, "dsl": dsl, "execution_plan": execution_plan}
