from app.parsers.extractors import extract_all
from app.parsers.intent_mapper import map_intents, infer_trigger_from_action
from app.parsers.rule_builder import build_final_rule
from app.parsers.validator import validate_rule
from app.parsers.cache import cache_store
from app.llm.service import parse_workflow_with_llm
from app.metrics.parser_metrics import parser_metrics
from app.core.logger import logger


def merge_patch(rule, patch):
    if not isinstance(patch, dict):
        return rule

    for key in ["trigger", "action"]:
        if rule.get(key) is None and patch.get(key):
            rule[key] = patch[key]

    if patch.get("conditions"):
        if not isinstance(rule.get("conditions"), list):
            rule["conditions"] = []
        rule["conditions"].extend(patch["conditions"])

    if patch.get("config"):
        if not isinstance(rule.get("config"), dict):
            rule["config"] = {}
        rule["config"].update(patch["config"])

    return rule


def _normalize_config(config: dict) -> dict:
    if not isinstance(config, dict):
        return {}

    normalized = {}

    if "retry" in config:
        normalized["retry_max"] = config["retry"]
    if "max_retry" in config:
        normalized["retry_max"] = config["max_retry"]
    if "retry_times" in config:
        normalized["retry_max"] = config["retry_times"]
    if "retry_max" in config:
        normalized["retry_max"] = config["retry_max"]

    if "timeout" in config:
        normalized["timeout_sec"] = config["timeout"]
    if "timeout_sec" in config:
        normalized["timeout_sec"] = config["timeout_sec"]

    return normalized


def _normalize_conditions(conds):
    if conds is None:
        return []

    if not isinstance(conds, list):
        conds = [conds]

    normalized = []
    for item in conds:
        if isinstance(item, dict):
            for k, v in item.items():
                normalized.append(f"{k}={v}")
        else:
            normalized.append(str(item).replace(" ", "").lower())

    return list(dict.fromkeys(normalized))


def enrich_rule(rule: dict, extracted: dict):
    rule = dict(rule or {})

    rule.setdefault("trigger", None)
    rule.setdefault("action", None)
    rule.setdefault("conditions", [])
    rule.setdefault("delay_days", None)
    rule.setdefault("entity_refs", {})
    rule.setdefault("config", {})

    if not isinstance(rule["conditions"], list):
        rule["conditions"] = []
    if not isinstance(rule["entity_refs"], dict):
        rule["entity_refs"] = {}
    if not isinstance(rule["config"], dict):
        rule["config"] = {}

    # delay
    if extracted.get("days") is not None and rule.get("delay_days") is None:
        rule["delay_days"] = extracted["days"]

    # entity refs
    refs = extracted.get("entity_refs", {})
    if isinstance(refs, dict):
        rule["entity_refs"].update(refs)

    # config
    extracted_config = _normalize_config(extracted.get("config", {}))
    rule["config"].update(extracted_config)

    # retry from repeat_count
    if extracted.get("repeat_count") is not None:
        rule["config"]["retry_max"] = extracted["repeat_count"]

    # flags → conditions
    flags = extracted.get("flags", {})
    if flags.get("vip"):
        rule["conditions"].append("vip=true")
    if flags.get("premium"):
        rule["conditions"].append("premium=true")

    # amount
    if extracted.get("amount_threshold") is not None:
        rule["conditions"].append(f"amount>{extracted['amount_threshold']}")

    # normalize
    rule["conditions"] = _normalize_conditions(rule["conditions"])

    # remove delay duplicates
    if rule.get("delay_days") is not None:
        rule["conditions"] = [
            c for c in rule["conditions"] if "days_since" not in c and "delay" not in c
        ]

    return rule


def canonicalize(rule: dict):
    allowed_keys = {
        "trigger",
        "action",
        "conditions",
        "delay_days",
        "config",
        "entity_refs",
    }

    rule = {k: v for k, v in dict(rule).items() if k in allowed_keys}

    cfg = rule.get("config", {})
    if isinstance(cfg, dict):
        cleaned_cfg = {
            "retry_max": cfg.get("retry_max"),
            "timeout_sec": cfg.get("timeout_sec"),
        }
        rule["config"] = {k: v for k, v in cleaned_cfg.items() if v is not None}

    return rule


def build_standard_response(
    success: bool,
    source: str,
    rule: dict,
    validation: dict,
    score: float,
    extracted: dict,
    mapped: dict,
):
    return {
        "success": success,
        "source": source,
        "rule": rule,
        "validation": validation,
        "debug": {
            "extracted": extracted,
            "mapped": mapped,
        },
        "score": score,
        "data": rule if success else None,
        "error": None if success else validation["errors"],
    }


def parse_workflow_text(text: str):
    parser_metrics.total_requests += 1
    if text in cache_store:
        parser_metrics.cache_hits += 1
        return cache_store[text]

    extracted = extract_all(text)
    mapped = map_intents(text)

    source = "rules"
    score = 1.0

    base_rule = build_final_rule(extracted=extracted, mapped=mapped)
    if base_rule.get("trigger") is None:
        base_rule["trigger"] = infer_trigger_from_action(base_rule.get("action"))

    needs_patch = base_rule.get("trigger") is None or base_rule.get("action") is None
    if needs_patch:
        logger.info("llm_patch_triggered")

        llm_result = parse_workflow_with_llm(text)

        if llm_result["success"] and llm_result.get("score", 0) >= 0.6:
            parser_metrics.llm_hits += 1

            patch = llm_result.get("data", {})
            base_rule = merge_patch(base_rule, patch)

            source = "llm_patch"
            score = llm_result.get("score", 0)
        else:
            parser_metrics.failures += 1
            parser_metrics.fallback_used += 1
            logger.warning("llm_patch_failed_or_low_score")

    final_rule = enrich_rule(base_rule, extracted)
    if final_rule.get("trigger") is None:
        final_rule["trigger"] = infer_trigger_from_action(final_rule.get("action"))

    final_rule = canonicalize(final_rule)

    validation = validate_rule(final_rule)

    result = build_standard_response(
        success=validation["is_valid"],
        source=source,
        rule=final_rule,
        validation=validation,
        score=score,
        extracted=extracted,
        mapped=mapped,
    )

    if not result["success"]:
        parser_metrics.failures += 1
        logger.warning("parse_validation_failed")
    else:
        parser_metrics.regex_hits += 1
        logger.info("parse_success")

    cache_store[text] = result

    return result
