"""
PART 4 — Provider Health Tracking

Tracks provider health state in memory.
Disables providers on fatal errors (API_KEY_INVALID, etc.)
with a cooldown before re-enabling.
"""

import time
from app.core.logger import logger

# Cooldown in seconds before a disabled provider is retried
DEFAULT_COOLDOWN_SECONDS = 300  # 5 minutes

# Fatal errors that permanently disable a provider until cooldown expires
FATAL_ERRORS = {
    "API_KEY_INVALID",
    "PERMISSION_DENIED",
    "QUOTA_EXCEEDED",
    "invalid api key",
    "api key not valid",
    "401",
    "403",
}

# In-memory provider state
# Structure: { provider_name: { "enabled": bool, "reason": str, "disabled_until": float } }
PROVIDER_STATE: dict = {}


def is_provider_healthy(provider_name: str) -> bool:
    """
    Returns True if provider is healthy and should be called.
    Returns False if disabled and cooldown has not expired.
    Re-enables provider if cooldown has expired.
    """
    state = PROVIDER_STATE.get(provider_name)

    if state is None:
        return True  # never seen — assume healthy

    if state.get("enabled", True):
        return True

    # Check if cooldown has expired
    disabled_until = state.get("disabled_until", 0)
    if time.time() >= disabled_until:
        # Cooldown expired — re-enable and let it try again
        PROVIDER_STATE[provider_name] = {"enabled": True, "reason": None, "disabled_until": 0}
        logger.info(
            "provider_reenabled_after_cooldown",
            extra={"extra_data": {"provider": provider_name}},
        )
        return True

    logger.info(
        "provider_skipped_unhealthy",
        extra={
            "extra_data": {
                "provider": provider_name,
                "reason": state.get("reason"),
                "disabled_until": disabled_until,
                "seconds_remaining": int(disabled_until - time.time()),
            }
        },
    )
    return False


def record_provider_error(provider_name: str, error: str, cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS):
    """
    Record a provider error. If the error is fatal, disable the provider
    with a cooldown.
    """
    error_lower = str(error).lower()
    is_fatal = any(fe.lower() in error_lower for fe in FATAL_ERRORS)

    if is_fatal:
        disabled_until = time.time() + cooldown_seconds
        PROVIDER_STATE[provider_name] = {
            "enabled": False,
            "reason": str(error)[:200],
            "disabled_until": disabled_until,
        }
        logger.warning(
            "provider_disabled",
            extra={
                "extra_data": {
                    "provider": provider_name,
                    "reason": str(error)[:200],
                    "cooldown_seconds": cooldown_seconds,
                    "disabled_until": disabled_until,
                }
            },
        )
    else:
        # Non-fatal error — log but don't disable
        logger.warning(
            "provider_error_non_fatal",
            extra={"extra_data": {"provider": provider_name, "error": str(error)[:200]}},
        )


def get_provider_state() -> dict:
    """Return current state of all providers. Useful for health endpoints."""
    return dict(PROVIDER_STATE)


def reset_provider(provider_name: str):
    """Manually re-enable a provider. For admin/testing use."""
    if provider_name in PROVIDER_STATE:
        PROVIDER_STATE[provider_name] = {"enabled": True, "reason": None, "disabled_until": 0}
        logger.info("provider_manually_reset", extra={"extra_data": {"provider": provider_name}})
