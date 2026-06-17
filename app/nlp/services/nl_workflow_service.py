"""
app/nlp/services/nl_workflow_service.py

Full NL → workflow generation pipeline:
  - CatalogMatcher → SuitabilityAgent → PromptBuilder
  - LLM call with 3-attempt retry loop + gemini fallback
  - Schema + workflow validation
  - WorkflowCompilerService → DSL → AST → compiled parsed_rule_json
  - Eval logging on every attempt (Phase 3)
  - Prompt versioning + auto-rollback (Phase 4/5)
"""

import time
from sqlalchemy.orm import Session

from app.nlp.catalog.matcher import CatalogMatcher
from app.nlp.suitability.suitability_agent import SuitabilityAgent
from app.nlp.prompts.builder import PromptBuilder, PROMPT_NAME
from app.nlp.prompts.prompt_context import PromptContext
from app.nlp.prompts.prompt_version_store import version_store
from app.workflow.workflow_generator import WorkflowGenerator
from app.workflow.workflow_schema_validator import WorkflowSchemaValidator
from app.workflow.workflow_validator import WorkflowValidator
from app.workflow.workflow_repair_service import WorkflowRepairService
from app.workflow.workflow_compiler_service import WorkflowCompilerService
from app.repositories import generation_log_repo
from app.core.logger import logger

MAX_RETRIES = 3
FALLBACK_PROVIDERS = ["gemini"]


class NLPWorkflowService:

    def __init__(
        self,
        catalog_matcher: CatalogMatcher,
        suitability_agent: SuitabilityAgent,
        prompt_builder: PromptBuilder,
        workflow_generator: WorkflowGenerator,
        schema_validator: WorkflowSchemaValidator,
        workflow_validator: WorkflowValidator,
        workflow_repair_service: WorkflowRepairService,
        compiler_service: WorkflowCompilerService,
        db: Session | None = None,
        domain: str | None = None,
    ):
        self.catalog_matcher = catalog_matcher
        self.suitability_agent = suitability_agent
        self.prompt_builder = prompt_builder
        self.workflow_generator = workflow_generator
        self.schema_validator = schema_validator
        self.workflow_validator = workflow_validator
        self.workflow_repair_service = workflow_repair_service
        self.compiler_service = compiler_service
        self._db = db
        self._domain = domain

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #

    def generate(self, user_request: str) -> dict:
        catalog_result = self.catalog_matcher.match(user_request)
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

        build_result = self.prompt_builder.build(context)
        prompt = build_result.prompt
        prompt_name = build_result.prompt_name
        prompt_version = build_result.version
        estimated_tokens = build_result.estimated_tokens

        last_errors = None
        last_raw = None
        current_prompt = prompt

        # ── Primary retry loop ─────────────────────────────────────────
        for attempt in range(1, MAX_RETRIES + 1):
            start = time.time()
            provider_used = None
            try:
                raw_result = self.workflow_generator.generate(current_prompt)
                provider_used = getattr(raw_result, "_provider", None)
            except RuntimeError as e:
                latency_ms = int((time.time() - start) * 1000)
                last_errors = [str(e)]
                self._log(user_request, prompt_name, prompt_version, estimated_tokens,
                          None, attempt, False, False, "llm_error", last_errors, latency_ms)
                self._track_failure(prompt_name, user_request)
                current_prompt = self.workflow_repair_service.repair(
                    raw_output="", validation_errors=last_errors, original_prompt=prompt)
                continue

            latency_ms = int((time.time() - start) * 1000)
            valid, outcome = self._validate_workflow(workflow_type, raw_result)

            if valid:
                self._log(user_request, prompt_name, prompt_version, estimated_tokens,
                          provider_used, attempt, False, True, None, None, latency_ms)
                version_store.record_success(prompt_name)
                return outcome

            last_errors = outcome
            last_raw = raw_result
            failure_reason = self._classify_failure(last_errors)
            self._log(user_request, prompt_name, prompt_version, estimated_tokens,
                      provider_used, attempt, False, False, failure_reason, last_errors, latency_ms)
            self._track_failure(prompt_name, user_request)
            current_prompt = self.workflow_repair_service.repair(
                raw_output=last_raw, validation_errors=last_errors, original_prompt=prompt)

        # ── Fallback providers ─────────────────────────────────────────
        for provider in FALLBACK_PROVIDERS:
            for fallback_attempt in range(1, 3):
                start = time.time()
                try:
                    raw_result = self.workflow_generator.generate_with_provider(
                        prompt if fallback_attempt == 1 else current_prompt, provider)
                except RuntimeError as e:
                    latency_ms = int((time.time() - start) * 1000)
                    last_errors = [str(e)]
                    self._log(user_request, prompt_name, prompt_version, estimated_tokens,
                              provider, MAX_RETRIES + fallback_attempt, True, False,
                              "llm_error", last_errors, latency_ms)
                    break

                latency_ms = int((time.time() - start) * 1000)
                valid, outcome = self._validate_workflow(workflow_type, raw_result)

                if valid:
                    self._log(user_request, prompt_name, prompt_version, estimated_tokens,
                              provider, MAX_RETRIES + fallback_attempt, True, True,
                              None, None, latency_ms)
                    version_store.record_success(prompt_name)
                    return outcome

                last_errors = outcome
                failure_reason = self._classify_failure(last_errors)
                self._log(user_request, prompt_name, prompt_version, estimated_tokens,
                          provider, MAX_RETRIES + fallback_attempt, True, False,
                          failure_reason, last_errors, latency_ms)
                current_prompt = self.workflow_repair_service.repair(
                    raw_output=raw_result, validation_errors=last_errors, original_prompt=prompt)

        logger.error("nl_workflow_all_attempts_exhausted",
                     extra={"extra_data": {"last_errors": last_errors}})
        raise ValueError(
            f"Workflow generation failed after {MAX_RETRIES} retries "
            f"and {len(FALLBACK_PROVIDERS)} fallback provider(s). "
            f"Last errors: {last_errors}"
        )

    # ------------------------------------------------------------------ #
    #  Validation + compile                                               #
    # ------------------------------------------------------------------ #

    def _validate_workflow(self, workflow_type: str, workflow: dict):
        schema_result = self.schema_validator.validate(workflow)
        if not schema_result.valid:
            return False, schema_result.errors

        wf_result = self.workflow_validator.validate(workflow)
        if not wf_result.valid:
            return False, wf_result.errors

        try:
            compile_result = self.compiler_service.compile(workflow_type, workflow)
        except Exception as e:
            return False, [str(e)]

        return True, compile_result

    # ------------------------------------------------------------------ #
    #  Auto-rollback                                                       #
    # ------------------------------------------------------------------ #

    def _track_failure(self, prompt_name: str, user_request: str) -> None:
        should_rollback = version_store.record_failure(prompt_name)
        if should_rollback:
            try:
                rolled_back_to = version_store.rollback(prompt_name)
                logger.warning("prompt_auto_rollback_triggered",
                               extra={"extra_data": {
                                   "prompt_name": prompt_name,
                                   "rolled_back_to": rolled_back_to,
                                   "user_request": user_request[:80],
                               }})
            except ValueError:
                pass

    # ------------------------------------------------------------------ #
    #  Eval logging                                                        #
    # ------------------------------------------------------------------ #

    def _log(self, user_request, prompt_name, prompt_version, estimated_tokens,
             provider, attempt_number, is_fallback, success, failure_reason,
             errors, latency_ms) -> None:
        if self._db is None:
            return
        generation_log_repo.save(
            self._db,
            user_request=user_request,
            domain=self._domain,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            estimated_tokens=estimated_tokens,
            provider=provider,
            attempt_number=attempt_number,
            is_fallback=is_fallback,
            success=success,
            failure_reason=failure_reason,
            errors=errors,
            latency_ms=latency_ms,
        )

    @staticmethod
    def _classify_failure(errors: list | None) -> str:
        if not errors:
            return "unknown"
        first = str(errors[0]).lower()
        if "schema" in first or "workflow_missing" in first:
            return "schema_fail"
        if "trigger" in first:
            return "trigger_fail"
        if "action" in first:
            return "action_fail"
        if "dsl" in first or "ast" in first or "compile" in first:
            return "compile_fail"
        if "dependency" in first or "circular" in first:
            return "dependency_fail"
        return "validation_fail"
