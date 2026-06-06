import time
from app.llm.prompt_loader import build_prompt
from app.llm.providers.ollama import try_call_ollama
from app.llm.providers.gemini_rest import try_call_gemini_rest
from app.llm.provider_health import is_provider_healthy, record_provider_error
from app.core.logger import logger

# PART 5 — Timeout hardening
# LLM repair path must fail fast — max 5 seconds total across all providers
LLM_REPAIR_TIMEOUT_SECONDS = 5


class LLMManager:
    def __init__(self):
        self.providers = [
            ("ollama", try_call_ollama),
            ("gemini", try_call_gemini_rest),
        ]

    def call(self, user_input: str, timeout_seconds: int = LLM_REPAIR_TIMEOUT_SECONDS):
        start = time.time()
        prompt = build_prompt("parser_v1.txt", {"user_input": user_input})
        errors = []

        for provider_name, provider_fn in self.providers:

            # PART 4 — skip unhealthy providers
            if not is_provider_healthy(provider_name):
                logger.info(
                    "provider_skipped_unhealthy",
                    extra={"extra_data": {"provider": provider_name}},
                )
                continue

            # PART 5 — fail fast if total budget exceeded
            elapsed = time.time() - start
            if elapsed >= timeout_seconds:
                logger.warning(
                    "llm_timeout_budget_exceeded",
                    extra={
                        "extra_data": {
                            "elapsed_seconds": round(elapsed, 2),
                            "timeout_seconds": timeout_seconds,
                        }
                    },
                )
                break

            logger.info(
                "llm_provider_attempt",
                extra={
                    "extra_data": {
                        "provider": provider_name,
                        "elapsed_ms": int(elapsed * 1000),
                    }
                },
            )

            result = provider_fn(prompt)

            if result["success"]:
                result["total_latency_ms"] = int((time.time() - start) * 1000)
                result["fallback_used"] = provider_name != self.providers[0][0]
                result["errors_before_success"] = errors

                if result["fallback_used"]:
                    logger.warning(
                        "llm_fallback_provider_used",
                        extra={
                            "extra_data": {
                                "provider": provider_name,
                                "prior_errors": errors,
                            }
                        },
                    )
                else:
                    logger.info(
                        "llm_provider_success",
                        extra={
                            "extra_data": {
                                "provider": provider_name,
                                "latency_ms": result["total_latency_ms"],
                            }
                        },
                    )
                return result

            # Record error for health tracking
            error_msg = result.get("error", "unknown")
            record_provider_error(provider_name, error_msg)

            logger.warning(
                "llm_provider_failed",
                extra={
                    "extra_data": {
                        "provider": provider_name,
                        "error": error_msg,
                    }
                },
            )
            errors.append({"provider": provider_name, "error": error_msg})

        total_ms = int((time.time() - start) * 1000)
        logger.error(
            "llm_all_providers_exhausted",
            extra={"extra_data": {"errors": errors, "total_latency_ms": total_ms}},
        )
        return {
            "success": False,
            "provider": None,
            "error": "all providers failed",
            "errors": errors,
            "total_latency_ms": total_ms,
        }
