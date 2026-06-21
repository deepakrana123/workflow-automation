

import time
import random
from app.core.logger import logger


# ─────────────────────────────────────────────────────────────
# CHAOS ENGINE
# ─────────────────────────────────────────────────────────────

class ChaosError(Exception):
    """Base class for all chaos-injected errors."""
    pass

class GatewayError(ChaosError):
    """502/503 — upstream service unavailable."""
    pass

class TimeoutError(ChaosError):
    """Request timed out — no response from third party."""
    pass

class RateLimitError(ChaosError):
    """429 — too many requests."""
    pass

class AuthError(ChaosError):
    """401/403 — invalid API key or token expired."""
    pass

class BadPayloadError(ChaosError):
    """400 — malformed or invalid request payload."""
    pass

class PartialSuccessError(ChaosError):
    """207 — some items succeeded, some failed."""
    pass


def _apply_chaos(action_name: str, payload: dict, config: dict):
    """
    Central chaos injection point.
    Reads chaos_mode from config and raises or returns accordingly.
    Returns None if no chaos — caller proceeds normally.
    """
    mode = config.get("chaos_mode", "success")
    attempt = payload.get("_attempt", 1)

    logger.info(
        "chaos_action_invoked",
        extra={
            "extra_data": {
                "action": action_name,
                "chaos_mode": mode,
                "attempt": attempt,
            }
        },
    )

    if mode == "success":
        return None  # no chaos

    if mode == "always_fail":
        raise GatewayError(f"[chaos:always_fail] {action_name} permanently unavailable")

    if mode == "timeout":
        delay = config.get("delay_seconds", 10)
        logger.warning(
            "chaos_timeout_simulated",
            extra={"extra_data": {"action": action_name, "delay_seconds": delay}},
        )
        time.sleep(delay)
        raise TimeoutError(f"[chaos:timeout] {action_name} timed out after {delay}s")

    if mode == "slow":
        delay = config.get("delay_seconds", 3)
        time.sleep(delay)
        return None  # slow but succeeds

    if mode == "gateway_error":
        raise GatewayError(f"[chaos:gateway_error] 502 Bad Gateway from {action_name}")

    if mode == "rate_limit":
        raise RateLimitError(f"[chaos:rate_limit] 429 Too Many Requests for {action_name}")

    if mode == "auth_error":
        raise AuthError(f"[chaos:auth_error] 401 Unauthorized — API key invalid for {action_name}")

    if mode == "bad_payload":
        raise BadPayloadError(f"[chaos:bad_payload] 400 Bad Request — invalid payload for {action_name}")

    if mode == "payload_overload":
        # Simulate receiving a massive response that causes processing issues
        huge = "x" * 100_000
        raise BadPayloadError(f"[chaos:payload_overload] response too large: {len(huge)} bytes")

    if mode == "partial_success":
        raise PartialSuccessError(f"[chaos:partial_success] 207 — partial failure in {action_name}")

    if mode == "flaky":
        fail_rate = config.get("fail_rate", 0.5)
        if random.random() < fail_rate:
            raise GatewayError(f"[chaos:flaky] {action_name} failed (rate={fail_rate})")
        return None  # this attempt succeeded

    if mode == "fail_on_attempt":
        target_attempt = config.get("fail_on_attempt", 1)
        if attempt == target_attempt:
            raise GatewayError(
                f"[chaos:fail_on_attempt] {action_name} failed on attempt {attempt}"
            )
        return None  # other attempts succeed

    if mode == "succeed_after_retries":
        # Fail for first N attempts, then succeed
        succeed_after = config.get("succeed_after", 2)
        if attempt <= succeed_after:
            raise GatewayError(
                f"[chaos:succeed_after_retries] failing attempt {attempt}/{succeed_after}"
            )
        return None  # succeeds after enough retries

    return None


def _chaos_response(action_name: str, extra: dict = None) -> dict:
    base = {"success": True, "status": "success", "action": action_name}
    if extra:
        base.update(extra)
    return base


# ─────────────────────────────────────────────────────────────
# CHAOS ACTIONS — drop-in replacements for real actions
# ─────────────────────────────────────────────────────────────

def chaos_send_reminder(payload: dict, config: dict) -> dict:
    """
    Simulates sending a reminder via SMS/email/push.
    Chaos modes: timeout, gateway_error, rate_limit, flaky, slow, always_fail
    """
    _apply_chaos("send_reminder", payload, config)
    logger.info("chaos_send_reminder_success", extra={"extra_data": {"payload": payload}})
    return _chaos_response("send_reminder", {"channel": config.get("channel", "email")})


def chaos_escalate_case(payload: dict, config: dict) -> dict:
    """
    Simulates escalating a case to a supervisor system.
    Chaos modes: gateway_error, auth_error, flaky, succeed_after_retries
    """
    _apply_chaos("escalate_case", payload, config)
    logger.info("chaos_escalate_case_success", extra={"extra_data": {"payload": payload}})
    return _chaos_response("escalate_case", {"escalated_to": "supervisor_queue"})


def chaos_notify_manager(payload: dict, config: dict) -> dict:
    """
    Simulates notifying a manager via webhook.
    Chaos modes: timeout, rate_limit, bad_payload, payload_overload
    """
    _apply_chaos("notify_manager", payload, config)
    logger.info("chaos_notify_manager_success", extra={"extra_data": {"payload": payload}})
    return _chaos_response("notify_manager", {"notified": True})


def chaos_reject_loan(payload: dict, config: dict) -> dict:
    """
    Simulates calling a loan rejection API.
    Chaos modes: auth_error, gateway_error, bad_payload, always_fail
    """
    _apply_chaos("reject_loan", payload, config)
    logger.info("chaos_reject_loan_success", extra={"extra_data": {"payload": payload}})
    return _chaos_response("reject_loan", {"loan_id": payload.get("entity_id")})


def chaos_close_case(payload: dict, config: dict) -> dict:
    """
    Simulates closing a support case.
    Chaos modes: flaky, succeed_after_retries, partial_success
    """
    _apply_chaos("close_case", payload, config)
    logger.info("chaos_close_case_success", extra={"extra_data": {"payload": payload}})
    return _chaos_response("close_case", {"closed": True})


def chaos_assign_senior_officer(payload: dict, config: dict) -> dict:
    """
    Simulates assigning to a senior officer via HR system API.
    Chaos modes: slow, timeout, gateway_error
    """
    _apply_chaos("assign_senior_officer", payload, config)
    logger.info("chaos_assign_senior_officer_success", extra={"extra_data": {"payload": payload}})
    return _chaos_response("assign_senior_officer", {"officer_id": "EMP_CHAOS_001"})
