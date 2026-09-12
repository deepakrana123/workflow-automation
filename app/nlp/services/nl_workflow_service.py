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
from app.prompting import PromptManager, PromptContext, PromptKey
from app.prompting.prompt_version_store import version_store
from app.workflow.workflow_generator import WorkflowGenerator
from app.workflow.workflow_schema_validator import WorkflowSchemaValidator
from app.workflow.workflow_validator import WorkflowValidator
from app.workflow.workflow_repair_service import WorkflowRepairService
from app.workflow.workflow_repair_service import _bare_name
from app.workflow.workflow_compiler_service import WorkflowCompilerService
from app.repositories import generation_log_repo
from app.core.logger import logger

MAX_RETRIES = 3
FALLBACK_PROVIDERS = ["groq", "openrouter", "openai", "gemini", "ollama"]


class NLPWorkflowService:

    def __init__(
        self,
        catalog_matcher: CatalogMatcher,
        suitability_agent: SuitabilityAgent,
        prompt_manager: PromptManager,
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
        self.prompt_manager = prompt_manager
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

    def generate(
        self,
        user_request: str,
        *,
        catalog_result=None,
        extra_variables: dict | None = None,
        prompt_version: str | None = None,
        progress_callback=None,
        budget_seconds: float = 30.0,
    ) -> dict:
        """Generate a workflow from a natural-language request.

        Args:
            user_request:       the NL instruction.
            catalog_result:     pre-computed candidate set. When None (global
                                path), the injected catalog_matcher is used.
            extra_variables:    additional prompt template variables.
            prompt_version:     pin a specific prompt version.
            progress_callback:  optional callable(event_name: str, data: dict).
                                Called at each pipeline stage. When None the
                                pipeline runs silently — no overhead, no change
                                in behaviour. The callback runs synchronously on
                                the same thread as generation so it must be fast
                                (e.g. push to a queue, never block).
            budget_seconds:     maximum wall-clock seconds for the entire
                                generation process across all attempts. Checked
                                before each LLM attempt. Raises ValueError with
                                code "generation_budget_exceeded" when breached.
        """
        generation_start = time.time()

        def _emit(event: str, data: dict) -> None:
            """Call progress_callback if one was provided. Never raises."""
            if progress_callback is not None:
                try:
                    progress_callback(event, data)
                except Exception:  # noqa: BLE001
                    pass

        def _budget_remaining() -> float:
            return max(0.0, budget_seconds - (time.time() - generation_start))

        def _check_budget(label: str) -> None:
            elapsed = time.time() - generation_start
            if elapsed >= budget_seconds:
                raise ValueError(
                    f"generation_budget_exceeded:{elapsed:.1f}s of {budget_seconds}s "
                    f"(exceeded before {label})"
                )

        if catalog_result is None:
            catalog_result = self.catalog_matcher.match(self._db, user_request)

        _emit("catalog_matched", {
            "action_count":  len(catalog_result.action_names),
            "trigger_count": len(catalog_result.trigger_names),
            "elapsed_ms":    int((time.time() - generation_start) * 1000),
        })

        workflow_type = catalog_result.workflow_type

        suitability = self.suitability_agent.evaluate(
            workflow_type,
            catalog_result.trigger_names,
            catalog_result.action_names,
        )
        if not suitability.supported:
            raise ValueError(suitability.reason)

        # Use the resolved workflow_type from suitability (handles None fallback)
        workflow_type = suitability.workflow_type or workflow_type or "general"

        # Store for use in _validate_workflow — catalog membership check
        self._current_catalog = catalog_result

        variables = {
            "workflow_type": workflow_type or "general",
            "triggers": "\n".join(catalog_result.trigger_names),
            "actions":  "\n".join(catalog_result.action_names),
            "user_request": user_request,
        }
        if extra_variables:
            variables.update(extra_variables)

        context = PromptContext(variables=variables)

        build_result = self.prompt_manager.build_with_metadata(
            PromptKey.WORKFLOW_GENERATION, context, version=prompt_version
        )
        prompt = build_result.prompt
        prompt_name = build_result.prompt_name
        prompt_version = prompt_version or build_result.version
        estimated_tokens = build_result.estimated_tokens

        last_errors = None
        last_raw = None
        current_prompt = prompt

        # Bare name sets for repair prompt — strip annotations once, reuse on every attempt
        bare_action_names  = [_bare_name(n) for n in catalog_result.action_names  if n]
        bare_trigger_names = [_bare_name(n) for n in catalog_result.trigger_names if n]

        # ── Primary retry loop ─────────────────────────────────────────
        for attempt in range(1, MAX_RETRIES + 1):

            # Budget check — before committing to another LLM call
            _check_budget(f"attempt {attempt}")

            _emit("llm_started", {
                "attempt":          attempt,
                "provider":         "primary",
                "budget_remaining_s": round(_budget_remaining(), 1),
            })

            start = time.time()
            provider_used = None
            try:
                raw_result = self.workflow_generator.generate(current_prompt)
                provider_used = getattr(raw_result, "_provider", None)
            except RuntimeError as e:
                latency_ms = int((time.time() - start) * 1000)
                last_errors = [str(e)]
                _emit("llm_attempt_failed", {
                    "attempt":    attempt,
                    "errors":     last_errors,
                    "elapsed_ms": latency_ms,
                })
                self._log(user_request, prompt_name, prompt_version, estimated_tokens,
                          None, attempt, False, False, "llm_error", last_errors, latency_ms)
                self._track_failure(prompt_name, user_request)
                current_prompt = self.workflow_repair_service.repair(
                    raw_output="",
                    validation_errors=last_errors,
                    original_prompt=prompt,
                    valid_action_names=bare_action_names,
                    valid_trigger_names=bare_trigger_names,
                )
                continue

            latency_ms = int((time.time() - start) * 1000)
            valid, outcome = self._validate_workflow(workflow_type, raw_result)

            if valid:
                _emit("llm_success", {
                    "attempt":    attempt,
                    "provider":   provider_used or "primary",
                    "elapsed_ms": latency_ms,
                })
                self._log(user_request, prompt_name, prompt_version, estimated_tokens,
                          provider_used, attempt, False, True, None, None, latency_ms)
                version_store.record_success(prompt_name)
                return outcome

            last_errors = outcome
            last_raw = raw_result
            failure_reason = self._classify_failure(last_errors)
            _emit("llm_attempt_failed", {
                "attempt":        attempt,
                "provider":       provider_used or "primary",
                "errors":         last_errors,
                "failure_reason": failure_reason,
                "elapsed_ms":     latency_ms,
            })
            self._log(user_request, prompt_name, prompt_version, estimated_tokens,
                      provider_used, attempt, False, False, failure_reason, last_errors, latency_ms)
            self._track_failure(prompt_name, user_request)
            current_prompt = self.workflow_repair_service.repair(
                raw_output=last_raw,
                validation_errors=last_errors,
                original_prompt=prompt,
                valid_action_names=bare_action_names,
                valid_trigger_names=bare_trigger_names,
            )

        # ── Fallback providers ─────────────────────────────────────────
        for provider in FALLBACK_PROVIDERS:
            for fallback_attempt in range(1, 3):

                # Budget check — before committing to a fallback LLM call
                _check_budget(f"fallback {provider} attempt {fallback_attempt}")

                _emit("llm_started", {
                    "attempt":            MAX_RETRIES + fallback_attempt,
                    "provider":           provider,
                    "budget_remaining_s": round(_budget_remaining(), 1),
                    "is_fallback":        True,
                })

                start = time.time()
                try:
                    raw_result = self.workflow_generator.generate_with_provider(
                        prompt if fallback_attempt == 1 else current_prompt, provider)
                except RuntimeError as e:
                    latency_ms = int((time.time() - start) * 1000)
                    last_errors = [str(e)]
                    _emit("llm_attempt_failed", {
                        "attempt":    MAX_RETRIES + fallback_attempt,
                        "provider":   provider,
                        "errors":     last_errors,
                        "elapsed_ms": latency_ms,
                        "is_fallback": True,
                    })
                    self._log(user_request, prompt_name, prompt_version, estimated_tokens,
                              provider, MAX_RETRIES + fallback_attempt, True, False,
                              "llm_error", last_errors, latency_ms)
                    break

                latency_ms = int((time.time() - start) * 1000)
                valid, outcome = self._validate_workflow(workflow_type, raw_result)

                if valid:
                    _emit("llm_success", {
                        "attempt":    MAX_RETRIES + fallback_attempt,
                        "provider":   provider,
                        "elapsed_ms": latency_ms,
                        "is_fallback": True,
                    })
                    self._log(user_request, prompt_name, prompt_version, estimated_tokens,
                              provider, MAX_RETRIES + fallback_attempt, True, True,
                              None, None, latency_ms)
                    version_store.record_success(prompt_name)
                    return outcome

                last_errors = outcome
                failure_reason = self._classify_failure(last_errors)
                _emit("llm_attempt_failed", {
                    "attempt":        MAX_RETRIES + fallback_attempt,
                    "provider":       provider,
                    "errors":         last_errors,
                    "failure_reason": failure_reason,
                    "elapsed_ms":     latency_ms,
                    "is_fallback":    True,
                })
                self._log(user_request, prompt_name, prompt_version, estimated_tokens,
                          provider, MAX_RETRIES + fallback_attempt, True, False,
                          failure_reason, last_errors, latency_ms)
                current_prompt = self.workflow_repair_service.repair(
                    raw_output=raw_result,
                    validation_errors=last_errors,
                    original_prompt=prompt,
                    valid_action_names=bare_action_names,
                    valid_trigger_names=bare_trigger_names,
                )

        total_elapsed_ms = int((time.time() - generation_start) * 1000)
        logger.error("nl_workflow_all_attempts_exhausted",
                     extra={"extra_data": {"last_errors": last_errors, "elapsed_ms": total_elapsed_ms}})
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

        # Build bare-name sets from the current catalog so the validator can
        # reject any action/trigger name the LLM hallucinated or annotated.
        catalog = getattr(self, "_current_catalog", None)
        valid_action_names  = set(getattr(catalog, "action_names",  []) or [])
        valid_trigger_names = set(getattr(catalog, "trigger_names", []) or [])

        wf_result = self.workflow_validator.validate(
            workflow,
            valid_action_names=valid_action_names or None,
            valid_trigger_names=valid_trigger_names or None,
        )
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
        if "trigger_not_in_catalog" in first:
            return "trigger_hallucinated"
        if "action_not_in_catalog" in first:
            return "action_hallucinated"
        if "trigger" in first:
            return "trigger_fail"
        if "action" in first:
            return "action_fail"
        if "llm_reported_error" in first:
            return "llm_error_response"
        if "dsl" in first or "ast" in first or "compile" in first:
            return "compile_fail"
        if "dependency" in first or "circular" in first or "dependencies_missing" in first:
            return "dependency_fail"
        return "validation_fail"
