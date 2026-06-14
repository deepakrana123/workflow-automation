from app.nlp.llm_manager.providers.gemini_rest import try_call_gemini_rest
from app.nlp.llm_manager.providers.ollama import try_call_ollama
from app.nlp.llm_manager import provider_health as health
from app.core.logger import logger


class LLMManager:

    def __init__(self):
        self.providers = [
            ("ollama", try_call_ollama),
            ("gemini", try_call_gemini_rest),
        ]
        self._provider_map = {name: fn for name, fn in self.providers}

    # ------------------------------------------------------------------ #
    #  Primary call — tries providers in order, skips unhealthy ones      #
    # ------------------------------------------------------------------ #

    def generate(self, prompt: str) -> dict:
        """
        Try providers in order (ollama → gemini).
        Skips providers that are currently disabled by health tracking.
        Returns the first successful result.
        Raises RuntimeError if all providers fail or are unhealthy.
        """
        last_error = "no healthy providers available"

        for provider_name, provider_fn in self.providers:

            if not health.is_healthy(provider_name):
                logger.info(
                    "provider_skipped",
                    extra={"extra_data": {"provider": provider_name}},
                )
                continue

            result = provider_fn(prompt)

            if result["success"]:
                health.record_success(provider_name)
                logger.info(
                    "llm_generate_success",
                    extra={
                        "extra_data": {
                            "provider": provider_name,
                            "latency_ms": result.get("latency_ms"),
                        }
                    },
                )
                return result

            # Failed — record against health tracker
            error_type = result.get("error_type", "unexpected")
            error_msg = result.get("error", "unknown")
            health.record_failure(provider_name, error_msg, error_type)
            last_error = f"{provider_name}: {error_msg}"

            logger.warning(
                "llm_provider_failed",
                extra={
                    "extra_data": {
                        "provider": provider_name,
                        "error_type": error_type,
                        "error": error_msg[:120],
                    }
                },
            )

        logger.error(
            "llm_all_providers_exhausted",
            extra={"extra_data": {"last_error": last_error}},
        )
        raise RuntimeError(f"All LLM providers failed. {last_error}")

    # ------------------------------------------------------------------ #
    #  Forced provider — used by fallback path in NLPWorkflowService      #
    # ------------------------------------------------------------------ #

    def generate_with_provider(self, prompt: str, provider: str) -> dict:
        """
        Force a specific provider, bypassing order but still respecting
        health state (will raise if provider is currently disabled).
        """
        provider_fn = self._provider_map.get(provider)
        if not provider_fn:
            raise ValueError(
                f"Unknown provider '{provider}'. "
                f"Available: {list(self._provider_map.keys())}"
            )

        if not health.is_healthy(provider):
            status = health.get_all_status().get(provider, {})
            remaining = status.get("cooldown_remaining_seconds", 0)
            raise RuntimeError(
                f"Provider '{provider}' is currently disabled. "
                f"Cooldown: {remaining}s remaining."
            )

        result = provider_fn(prompt)
        result["provider"] = provider

        if result["success"]:
            health.record_success(provider)
        else:
            error_type = result.get("error_type", "unexpected")
            health.record_failure(provider, result.get("error", "unknown"), error_type)

        return result

    # ------------------------------------------------------------------ #
    #  Health status — exposed via /api/health/providers                  #
    # ------------------------------------------------------------------ #

    def get_health_status(self) -> dict:
        return health.get_all_status()

    def reset_provider(self, provider: str) -> None:
        health.reset_provider(provider)
