import re

OPERATORS = {
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    "==": lambda a, b: a == b,
    "=": lambda a, b: str(a).lower() == str(b).lower(),
}

# Order matters — longer operators must be tried before shorter ones
# e.g. ">=" before ">" to avoid partial match
_OPERATOR_PATTERN = re.compile(r"(>=|<=|>|<|==|=)")


def _parse_condition_string(cond: str):
    """
    Parse a condition string like:
      "amount>5000"       → field="amount", op=">",  value=5000
      "vip=true"          → field="vip",    op="=",  value="true"
      "repeat_count>=3"   → field="repeat_count", op=">=", value=3
    Returns (field, operator_fn, expected_value) or None if unparseable.
    """
    match = _OPERATOR_PATTERN.search(cond)
    if not match:
        return None

    op_str = match.group(1)
    field = cond[: match.start()].strip()
    raw_value = cond[match.end() :].strip()
    try:
        value = int(raw_value)
    except ValueError:
        try:
            value = float(raw_value)
        except ValueError:
            value = raw_value  # keep as string (e.g. "true", "vip")

    fn = OPERATORS.get(op_str)
    if not fn:
        return None

    return field, fn, value


def is_rule_matched(rule: dict, event: dict, data: dict) -> bool:
    if rule.get("trigger") != event["event_type"]:
        return False

    conditions = rule.get("conditions", [])

    for cond in conditions:
        if isinstance(cond, dict):
            field = cond["field"]
            op_str = cond["operator"]
            expected = cond["value"]
            fn = OPERATORS.get(op_str)
            if not fn:
                return False
            actual = data.get(field)
            if not fn(actual, expected):
                return False

        elif isinstance(cond, str):
            parsed = _parse_condition_string(cond)
            if parsed is None:
                continue
            field, fn, expected = parsed
            actual = data.get(field)
            if actual is None:
                return False
            try:
                if not fn(actual, expected):
                    return False
            except TypeError:
                return False

    return True
