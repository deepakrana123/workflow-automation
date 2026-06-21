"""
app/nlp/llm_manager/provider_health.py

In-memory provider health state.

Rules:
- 3 consecutive failures  → provider disabled, 5-minute cooldown
- auth_error              → provider disabled immediately, 30-minute cooldown
- success                 → failure count reset, provider re-enabled
- cooldown expired        → provider re-enabled automatically on next check

Thread-safety: single-process only. Good enough for current architecture.
If you move to multi-worker, back this with Redis.
"""

import time
from app.core.logger import logger

# Consecutive failures before a provider is disabled
FAILURE_THRESHOLD = 3

# Cooldown periods by error type (seconds)
COOLDOWN = {
    "auth_error":       30 * 60,   # 30 minutes — API key / quota issue
    "default":           5 * 60,   # 5 minutes  — timeout / connection / http
}

# Error types that trigger immediate disable (single occurrence)
IMMEDIATE_DISABLE_ERRORS = {"auth_error"}

# In-memory state
# { provider_name: { enabled, failure_count, disabled_until, last_error, last_error_type } }
_state: dict[str, dict] = {}


def _get(provider: str) -> dict:
    if provider not in _state:
        _state[provider] = {
            "enabled": True,
            "failure_count": 0,
            "disabled_until": 0.0,
            "last_error": None,
            "last_error_type": None,
        }
    return _state[provider]


def is_healthy(provider: str) -> bool:
    """
    Returns True if the provider should be called.
    Auto re-enables if the cooldown has expired.
    """
    state = _get(provider)

    if state["enabled"]:
        return True

    # Check if cooldown expired
    if time.time() >= state["disabled_until"]:
        state["enabled"] = True
        state["failure_count"] = 0
        state["last_error"] = None
        state["last_error_type"] = None
        logger.info(
            "provider_reenabled_after_cooldown",
            extra={"extra_data": {"provider": provider}},
        )
        return True

    remaining = int(state["disabled_until"] - time.time())
    logger.info(
        "provider_skipped_unhealthy",
        extra={
            "extra_data": {
                "provider": provider,
                "cooldown_remaining_seconds": remaining,
                "last_error_type": state["last_error_type"],
            }
        },
    )
    return False


def record_success(provider: str) -> None:
    """Reset failure count on a successful call."""
    state = _get(provider)
    if state["failure_count"] > 0:
        logger.info(
            "provider_recovered",
            extra={
                "extra_data": {
                    "provider": provider,
                    "previous_failure_count": state["failure_count"],
                }
            },
        )
    state["enabled"] = True
    state["failure_count"] = 0
    state["last_error"] = None
    state["last_error_type"] = None


def record_failure(provider: str, error: str, error_type: str = "unexpected") -> None:
    """
    Record a provider failure.
    Disables the provider if failure threshold is reached or error is fatal.
    """
    state = _get(provider)
    state["last_error"] = error[:200]
    state["last_error_type"] = error_type

    # Immediate disable for fatal error types
    if error_type in IMMEDIATE_DISABLE_ERRORS:
        cooldown = COOLDOWN["auth_error"]
        state["enabled"] = False
        state["failure_count"] = FAILURE_THRESHOLD
        state["disabled_until"] = time.time() + cooldown
        logger.warning(
            "provider_disabled_fatal_error",
            extra={
                "extra_data": {
                    "provider": provider,
                    "error_type": error_type,
                    "cooldown_seconds": cooldown,
                }
            },
        )
        return

    state["failure_count"] += 1

    if state["failure_count"] >= FAILURE_THRESHOLD:
        cooldown = COOLDOWN["default"]
        state["enabled"] = False
        state["disabled_until"] = time.time() + cooldown
        logger.warning(
            "provider_disabled_threshold_reached",
            extra={
                "extra_data": {
                    "provider": provider,
                    "failure_count": state["failure_count"],
                    "cooldown_seconds": cooldown,
                    "last_error_type": error_type,
                }
            },
        )
    else:
        logger.warning(
            "provider_failure_recorded",
            extra={
                "extra_data": {
                    "provider": provider,
                    "failure_count": state["failure_count"],
                    "threshold": FAILURE_THRESHOLD,
                    "error_type": error_type,
                }
            },
        )


def get_all_status() -> dict:
    """
    Return health status of all known providers.
    Used by GET /api/health/providers.
    """
    result = {}
    for provider, state in _state.items():
        disabled_until = state["disabled_until"]
        cooldown_remaining = (
            max(0, int(disabled_until - time.time()))
            if not state["enabled"] and disabled_until > 0
            else 0
        )
        result[provider] = {
            "enabled": state["enabled"],
            "failure_count": state["failure_count"],
            "last_error": state["last_error"],
            "last_error_type": state["last_error_type"],
            "cooldown_remaining_seconds": cooldown_remaining,
        }
    return result


def reset_provider(provider: str) -> None:
    """Manually re-enable a provider. For admin / testing use."""
    if provider in _state:
        _state[provider] = {
            "enabled": True,
            "failure_count": 0,
            "disabled_until": 0.0,
            "last_error": None,
            "last_error_type": None,
        }
        logger.info(
            "provider_manually_reset",
            extra={"extra_data": {"provider": provider}},
        )
