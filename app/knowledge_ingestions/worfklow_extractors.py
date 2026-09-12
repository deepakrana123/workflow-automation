# from pydantic import ValidationError

# from app.nlp.llm_manager.llm_manager import LLMManager
# from app.nlp.llm_manager import provider_health as health
# from app.knowledge_ingestions.schemas import WorkflowExtraction
# from app.knowledge_ingestions.exceptions import WorkflowExtractionError
# from app.core.logger import logger

# from app.prompting import PromptManager, PromptContext, PromptKey


# # ── Compact output example ────────────────────────────────────────────────────
# # Passed to the LLM as {schema} instead of model_json_schema().
# #
# # Why: Pydantic's model_json_schema() emits a verbose $defs-heavy JSON Schema
# # object. Smaller models (GPT-4o-mini, Llama) confuse it with the expected
# # output and echo the schema back instead of filling it. A concrete filled
# # example is unambiguous — the model sees exactly what shape to return.
# #
# # The example deliberately shows 7+ actions and 5+ rules to signal that
# # exhaustive extraction is expected — not a brief summary.
# _OUTPUT_EXAMPLE = """{
#   "workflow_name": "Example Workflow",
#   "summary": "Short summary based only on the source document.",
#   "triggers": [
#     {
#       "name": "Example Trigger",
#       "description": "Example description.",
#       "applicable_rules": [],
#       "responsible_actors": []
#     }
#   ],
#   "action_references": [
#     {
#       "name": "Example Action",
#       "description": "Example action description.",
#       "applicable_rules": [],
#       "responsible_actors": []
#     }
#   ],
#   "business_rules": [
#     {
#       "rule": "Example business rule.",
#       "condition": "Example condition.",
#       "outcome": "Example outcome.",
#       "responsible_role": "Example role.",
#       "threshold": "Example threshold."
#     }
#   ],
#   "actors": [
#     {
#       "name": "Example Actor",
#       "role": "Example Role"
#     }
#   ],
#   "external_systems": [
#     {
#       "name": "Example External System",
#       "description": "Example business purpose."
#     }
#   ],
#   "assumptions": [
#     "Example assumption explicitly marked as an assumption."
#   ]
# }
# IMPORTANT:
# This JSON is a STRUCTURAL EXAMPLE ONLY.

# All names, descriptions, rules, thresholds, actors, systems,
# and values in the example are fictional.

# DO NOT copy or reuse any value from this example.
# DO NOT infer business facts from this example.

# The source BRD is the ONLY authority for extracted content.
# """


# class WorkflowExtractor:
#     def __init__(self):
#         self.prompt_manager = PromptManager()
#         self._llm = LLMManager()

#     def extract(self, document_text: str) -> WorkflowExtraction:
#         if not document_text.strip():
#             raise WorkflowExtractionError("Document text is empty.")

#         prompt = self.prompt_manager.build(
#             PromptKey.WORKFLOW_EXTRACTION,
#             PromptContext(
#                 variables={
#                     "schema": _OUTPUT_EXAMPLE,
#                     "text": document_text,
#                 }
#             ),
#         )

#         # Provider selection for BRD extraction:
#         #
#         #   1. Gemini — preferred: large context window, 90s timeout, best at
#         #      exhaustive multi-item extraction. Skipped if currently unhealthy
#         #      (i.e. recently returned 429 or other http_error).
#         #
#         #   2. OpenRouter — first fallback: GPT-4o-mini via OpenRouter, reliable
#         #      and fast. Used whenever Gemini is rate-limited or down.
#         #
#         #   3. Standard waterfall — last resort: tries the remaining providers
#         #      in LLMManager order (openai, ollama).
#         #
#         # We check health before attempting Gemini to avoid a wasted 429 round-trip.

#         result = None

#         # ── Attempt 1: Gemini (if healthy) ───────────────────────────────────
#         if health.is_healthy("gemini"):
#             try:
#                 result = self._llm.generate_with_provider(prompt, "gemini")
#                 if not result.get("success"):
#                     logger.warning(
#                         "workflow_extractor_gemini_failed",
#                         extra={"extra_data": {
#                             "error_type": result.get("error_type"),
#                             "error":      result.get("error", "")[:120],
#                         }},
#                     )
#                     result = None
#             except Exception as exc:
#                 logger.warning(
#                     "workflow_extractor_gemini_exception",
#                     extra={"extra_data": {"error": str(exc)[:120]}},
#                 )
#                 result = None
#         else:
#             logger.info(
#                 "workflow_extractor_gemini_skipped_unhealthy",
#                 extra={"extra_data": {
#                     "cooldown": health.get_all_status().get("gemini", {}).get(
#                         "cooldown_remaining_seconds", 0
#                     )
#                 }},
#             )

#         # ── Attempt 2: OpenRouter (if Gemini failed/skipped) ─────────────────
#         if result is None and health.is_healthy("openrouter"):
#             try:
#                 result = self._llm.generate_with_provider(prompt, "openrouter")
#                 if not result.get("success"):
#                     logger.warning(
#                         "workflow_extractor_openrouter_failed",
#                         extra={"extra_data": {
#                             "error_type": result.get("error_type"),
#                             "error":      result.get("error", "")[:120],
#                         }},
#                     )
#                     result = None
#             except Exception as exc:
#                 logger.warning(
#                     "workflow_extractor_openrouter_exception",
#                     extra={"extra_data": {"error": str(exc)[:120]}},
#                 )
#                 result = None

#         # ── Attempt 3: remaining waterfall ───────────────────────────────────
#         if result is None:
#             result = self._llm.generate(prompt)

#         if not result["success"]:
#             raise WorkflowExtractionError(result.get("error", "LLM call failed"))

#         try:
#             extraction = WorkflowExtraction.model_validate_json(result["output"])
#             logger.info(
#                 "workflow_extraction_complete",
#                 extra={"extra_data": {
#                     "provider":           result.get("provider"),
#                     "actions_extracted":  len(extraction.action_references),
#                     "rules_extracted":    len(extraction.business_rules),
#                     "triggers_extracted": len(extraction.triggers),
#                     "workflow_name":      extraction.workflow_name,
#                 }},
#             )
#             return extraction

#         except ValidationError as e:
#             raise WorkflowExtractionError(
#                 f"Invalid workflow extraction: {e}"
#             ) from e



from pathlib import Path

from pydantic import ValidationError

from app.nlp.llm_manager.llm_manager import LLMManager
from app.nlp.llm_manager import provider_health as health
from app.knowledge_ingestions.schemas import WorkflowExtraction
from app.knowledge_ingestions.exceptions import WorkflowExtractionError
from app.core.logger import logger
from app.prompting import PromptManager, PromptContext, PromptKey


# ── Compact structural output example ────────────────────────────────────────
#
# Passed to the LLM as {schema} instead of model_json_schema().
#
# IMPORTANT:
# This is only a structural example.
# It must never provide real business facts to the model.
#

_OUTPUT_EXAMPLE = """{
  "workflow_name": "Example Workflow",
  "summary": "Short summary based only on the source document.",
  "triggers": [
    {
      "name": "Example Trigger",
      "description": "Example description.",
      "applicable_rules": [],
      "responsible_actors": []
    }
  ],
  "action_references": [
    {
      "name": "Example Action",
      "description": "Example action description.",
      "applicable_rules": [],
      "responsible_actors": []
    }
  ],
  "business_rules": [
    {
      "rule": "Example business rule.",
      "condition": "Example condition.",
      "outcome": "Example outcome.",
      "responsible_role": "Example role.",
      "threshold": "Example threshold."
    }
  ],
  "actors": [
    {
      "name": "Example Actor",
      "role": "Example Role"
    }
  ],
  "external_systems": [
    {
      "name": "Example External System",
      "description": "Example business purpose."
    }
  ],
  "assumptions": [
    "Example assumption explicitly marked as an assumption."
  ]
}

IMPORTANT:

This JSON is a STRUCTURAL EXAMPLE ONLY.

All names, descriptions, rules, thresholds, actors, systems,
and values in the example are fictional.

DO NOT copy or reuse any value from this example.
DO NOT infer business facts from this example.

The source BRD is the ONLY authority for extracted content.
"""


# ── Debug output directory ────────────────────────────────────────────────────
#
# Temporary observability artifacts.
# These let us inspect exactly what reached the workflow LLM.
#

_DEBUG_DIR = Path("debug_workflow_extraction")


class WorkflowExtractor:

    def __init__(self):
        self.prompt_manager = PromptManager()
        self._llm = LLMManager()

    def extract(self, document_text: str) -> WorkflowExtraction:

        # ── Input validation ────────────────────────────────────────────────

        if not document_text.strip():
            raise WorkflowExtractionError("Document text is empty.")

        document_text = document_text.strip()

        logger.info(
            "workflow_extractor_input",
            extra={
                "extra_data": {
                    "input_chars": len(document_text),
                    "input_lines": len(document_text.splitlines()),
                }
            },
        )

        # ── Build prompt ───────────────────────────────────────────────────

        prompt = self.prompt_manager.build(
            PromptKey.WORKFLOW_EXTRACTION,
            PromptContext(
                variables={
                    "schema": _OUTPUT_EXAMPLE,
                    "text": document_text,
                }
            ),
        )

        logger.info(
            "workflow_extractor_prompt_built",
            extra={
                "extra_data": {
                    "document_chars": len(document_text),
                    "prompt_chars": len(prompt),
                }
            },
        )

        # Save exact workflow input for debugging.
        #
        # IMPORTANT:
        # This is intentionally saved to a local debug directory,
        # not printed into application logs.
        self._save_debug_input(prompt)

        result = None

        # ── Attempt 1: Gemini ───────────────────────────────────────────────
        #
        # Gemini is preferred because of its larger context window and
        # suitability for exhaustive document extraction.
        #

        if health.is_healthy("gemini"):

            logger.info(
                "workflow_extractor_provider_attempt",
                extra={
                    "extra_data": {
                        "provider": "gemini",
                        "prompt_chars": len(prompt),
                    }
                },
            )

            try:
                result = self._llm.generate_with_provider(
                    prompt,
                    "gemini",
                )

                if result.get("success"):

                    logger.info(
                        "workflow_extractor_provider_success",
                        extra={
                            "extra_data": {
                                "provider": "gemini",
                                "output_chars": len(
                                    result.get("output", "")
                                ),
                            }
                        },
                    )

                else:

                    logger.warning(
                        "workflow_extractor_gemini_failed",
                        extra={
                            "extra_data": {
                                "error_type": result.get("error_type"),
                                "error": result.get("error", "")[:120],
                            }
                        },
                    )

                    result = None

            except Exception as exc:

                logger.warning(
                    "workflow_extractor_gemini_exception",
                    extra={
                        "extra_data": {
                            "error": str(exc)[:120],
                        }
                    },
                )

                result = None

        else:

            cooldown = (
                health.get_all_status()
                .get("gemini", {})
                .get("cooldown_remaining_seconds", 0)
            )

            logger.info(
                "workflow_extractor_gemini_skipped_unhealthy",
                extra={
                    "extra_data": {
                        "cooldown_remaining_seconds": cooldown,
                    }
                },
            )

        # ── Attempt 2: OpenRouter ──────────────────────────────────────────

        if result is None and health.is_healthy("openrouter"):

            logger.info(
                "workflow_extractor_provider_attempt",
                extra={
                    "extra_data": {
                        "provider": "openrouter",
                        "prompt_chars": len(prompt),
                    }
                },
            )

            try:

                result = self._llm.generate_with_provider(
                    prompt,
                    "openrouter",
                )

                if result.get("success"):

                    logger.info(
                        "workflow_extractor_provider_success",
                        extra={
                            "extra_data": {
                                "provider": "openrouter",
                                "output_chars": len(
                                    result.get("output", "")
                                ),
                            }
                        },
                    )

                else:

                    logger.warning(
                        "workflow_extractor_openrouter_failed",
                        extra={
                            "extra_data": {
                                "error_type": result.get("error_type"),
                                "error": result.get("error", "")[:120],
                            }
                        },
                    )

                    result = None

            except Exception as exc:

                logger.warning(
                    "workflow_extractor_openrouter_exception",
                    extra={
                        "extra_data": {
                            "error": str(exc)[:120],
                        }
                    },
                )

                result = None

        # ── Attempt 3: remaining LLM waterfall ─────────────────────────────

        if result is None:

            logger.info(
                "workflow_extractor_provider_attempt",
                extra={
                    "extra_data": {
                        "provider": "llm_manager_waterfall",
                        "prompt_chars": len(prompt),
                    }
                },
            )

            try:

                result = self._llm.generate(prompt)

                if result.get("success"):

                    logger.info(
                        "workflow_extractor_provider_success",
                        extra={
                            "extra_data": {
                                "provider": result.get("provider"),
                                "output_chars": len(
                                    result.get("output", "")
                                ),
                            }
                        },
                    )

                else:

                    logger.warning(
                        "workflow_extractor_waterfall_failed",
                        extra={
                            "extra_data": {
                                "provider": result.get("provider"),
                                "error_type": result.get("error_type"),
                                "error": result.get("error", "")[:120],
                            }
                        },
                    )

            except Exception as exc:

                logger.exception(
                    "workflow_extractor_waterfall_exception",
                )

                raise WorkflowExtractionError(
                    f"LLM provider waterfall failed: {exc}"
                ) from exc

        # ── Final provider failure ─────────────────────────────────────────

        if not result or not result.get("success"):

            raise WorkflowExtractionError(
                result.get("error", "LLM call failed")
                if result
                else "LLM call failed with no result."
            )

        raw_output = result.get("output", "")

        logger.info(
            "workflow_extractor_raw_output",
            extra={
                "extra_data": {
                    "provider": result.get("provider"),
                    "output_chars": len(raw_output),
                }
            },
        )

        # Save exact raw LLM output before Pydantic validation.
        self._save_debug_output(raw_output)

        # ── Parse + validate ───────────────────────────────────────────────

        try:

            extraction = WorkflowExtraction.model_validate_json(
                raw_output
            )

        except ValidationError as exc:

            logger.error(
                "workflow_extractor_validation_failed",
                extra={
                    "extra_data": {
                        "provider": result.get("provider"),
                        "output_chars": len(raw_output),
                        "validation_errors": len(exc.errors()),
                    }
                },
            )

            raise WorkflowExtractionError(
                f"Invalid workflow extraction: {exc}"
            ) from exc

        # ── Final extraction metrics ───────────────────────────────────────

        logger.info(
            "workflow_extraction_complete",
            extra={
                "extra_data": {
                    "provider": result.get("provider"),
                    "input_chars": len(document_text),
                    "prompt_chars": len(prompt),
                    "output_chars": len(raw_output),
                    "actions_extracted": len(
                        extraction.action_references
                    ),
                    "rules_extracted": len(
                        extraction.business_rules
                    ),
                    "triggers_extracted": len(
                        extraction.triggers
                    ),
                    "actors_extracted": len(
                        extraction.actors
                    ),
                    "external_systems_extracted": len(
                        extraction.external_systems
                    ),
                    "assumptions_extracted": len(
                        extraction.assumptions
                    ),
                    "workflow_name": extraction.workflow_name,
                }
            },
        )

        # Save normalized structured result as well.
        self._save_debug_json(extraction)

        return extraction

    # ── Debug helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _ensure_debug_dir() -> None:
        _DEBUG_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

    @classmethod
    def _save_debug_input(cls, prompt: str) -> None:
        try:

            cls._ensure_debug_dir()

            path = _DEBUG_DIR / "workflow_llm_input.txt"

            path.write_text(
                prompt,
                encoding="utf-8",
            )

            logger.info(
                "workflow_debug_input_saved",
                extra={
                    "extra_data": {
                        "path": str(path),
                        "chars": len(prompt),
                    }
                },
            )

        except Exception as exc:

            # Debug artifact failure must NEVER break extraction.
            logger.warning(
                "workflow_debug_input_save_failed",
                extra={
                    "extra_data": {
                        "error": str(exc)[:120],
                    }
                },
            )

    @classmethod
    def _save_debug_output(cls, output: str) -> None:
        try:

            cls._ensure_debug_dir()

            path = _DEBUG_DIR / "workflow_llm_output.txt"

            path.write_text(
                output,
                encoding="utf-8",
            )

            logger.info(
                "workflow_debug_output_saved",
                extra={
                    "extra_data": {
                        "path": str(path),
                        "chars": len(output),
                    }
                },
            )

        except Exception as exc:

            logger.warning(
                "workflow_debug_output_save_failed",
                extra={
                    "extra_data": {
                        "error": str(exc)[:120],
                    }
                },
            )

    @classmethod
    def _save_debug_json(
        cls,
        extraction: WorkflowExtraction,
    ) -> None:
        try:

            cls._ensure_debug_dir()

            path = _DEBUG_DIR / "workflow_extraction.json"

            path.write_text(
                extraction.model_dump_json(indent=2),
                encoding="utf-8",
            )

            logger.info(
                "workflow_debug_json_saved",
                extra={
                    "extra_data": {
                        "path": str(path),
                    }
                },
            )

        except Exception as exc:

            logger.warning(
                "workflow_debug_json_save_failed",
                extra={
                    "extra_data": {
                        "error": str(exc)[:120],
                    }
                },
            )