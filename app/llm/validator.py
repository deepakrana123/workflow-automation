from app.llm.schemas import (
    ALLOWED_TRIGGERS,
    ALLOWED_ACTIONS,
    REQUIRED_FIELDS,
)
from app.core.logger import logger


def validate_workflow_json(data: dict):
    errors = []
    cleaned = {}

    if not isinstance(data, dict):
        return {"is_valid": False, "errors": ["response must be object"], "data": None}

    logger.debug("llm_validator_input", extra={"extra_data": {"data": data}})
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing field: {field}")

    trigger = data.get("trigger")
    if trigger not in ALLOWED_TRIGGERS:
        errors.append("invalid trigger")
    cleaned["trigger"] = trigger
    action = data.get("action")
    if action not in ALLOWED_ACTIONS:
        errors.append("invalid action")
    cleaned["action"] = action
    conditions = data.get("conditions", [])
    if not isinstance(conditions, list):
        conditions = [str(conditions)]
    conditions = [
        str(c).replace(" ", "").lower()
        for c in conditions
        if not any(x in str(c) for x in ["field=", "operator=", "value="])
    ]

    cleaned["conditions"] = list(dict.fromkeys(conditions))
    delay = data.get("delay_days")
    if delay is not None:
        try:
            delay = int(delay)
            if delay < 0:
                errors.append("delay_days cannot be negative")
            elif delay > 365:
                errors.append("delay_days too large")
        except Exception:
            errors.append("delay must be integer")
            delay = None

    cleaned["delay_days"] = delay
    raw_config = data.get("config", {})
    if not isinstance(raw_config, dict):
        raw_config = {}

    retry_val = (
        raw_config.get("retry")
        or raw_config.get("retry_times")
        or raw_config.get("max_retry")
        or raw_config.get("retry_max")
    )

    timeout_val = raw_config.get("timeout") or raw_config.get("timeout_sec")

    normalized_config = {}

    if retry_val is not None:
        try:
            normalized_config["retry_max"] = int(retry_val)
        except Exception:
            errors.append("invalid retry value")

    if timeout_val is not None:
        try:
            normalized_config["timeout_sec"] = int(timeout_val)
        except Exception:
            errors.append("invalid timeout value")

    cleaned["config"] = normalized_config
    entity_refs = data.get("entity_refs", {})
    if not isinstance(entity_refs, dict):
        entity_refs = {}

    cleaned["entity_refs"] = entity_refs
    is_valid = len(errors) == 0

    result = {
        "is_valid": is_valid,
        "errors": errors,
        "data": cleaned if is_valid else None,
    }

    if not is_valid:
        logger.warning(
            "llm_validator_failed",
            extra={"extra_data": {"errors": errors}},
        )

    return result


def score_response(rule: dict):
    if not isinstance(rule, dict):
        return 0.0

    score = 0.0

    if "trigger" in rule:
        score += 0.2
    if "action" in rule:
        score += 0.2
    if "conditions" in rule:
        score += 0.1
    if "config" in rule:
        score += 0.1

    if rule.get("trigger") in ALLOWED_TRIGGERS:
        score += 0.2
    else:
        score -= 0.2

    if rule.get("action") in ALLOWED_ACTIONS:
        score += 0.2
    else:
        score -= 0.2

    if rule.get("action") == "send_reminder" and rule.get("trigger") == "payment_due":
        score += 0.1

    if rule.get("action") in ["assign_senior_officer", "escalate_case"] and rule.get(
        "trigger"
    ) in ["ticket_created", "complaint_created"]:
        score += 0.1

    if (
        rule.get("action") in ["reject_loan", "notify_manager"]
        and rule.get("trigger") == "loan_requested"
    ):
        score += 0.1

    return max(0.0, min(score, 1.0))
