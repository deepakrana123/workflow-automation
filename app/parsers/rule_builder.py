from app.parsers.intent_mapper import infer_trigger_from_action


def build_conditions(extracted: dict):
    conditions = []
    flags = extracted.get("flags", {})

    if flags.get("vip"):
        conditions.append("vip=true")

    if flags.get("premium"):
        conditions.append("premium=true")

    if extracted.get("repeat_count") is not None:
        conditions.append(f"repeat_count>={extracted['repeat_count']}")

    if extracted.get("amount_threshold") is not None:
        conditions.append(f"amount>{extracted['amount_threshold']}")

    return conditions


def apply_defaults(rule: dict):
    action = rule.get("action")
    trigger = rule.get("trigger")

    if trigger:
        return rule

    # Use centralized inference logic
    inferred = infer_trigger_from_action(action)
    if inferred:
        rule["trigger"] = inferred

    return rule


def build_final_rule(extracted: dict, mapped: dict):
    rule = {
        "trigger": mapped["trigger_result"]["trigger"],
        "action": mapped["action_result"]["action"],
        "conditions": build_conditions(extracted),
        "delay_days": extracted.get("days"),
    }

    return apply_defaults(rule)
