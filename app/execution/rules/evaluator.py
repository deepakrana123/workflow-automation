"""
app/execution/rules/evaluator.py

evaluate_condition — the single-condition primitive of the rule engine.

A condition is ``{"op": "<operator>", "value": <expected>}`` evaluated against
an ``actual`` value (a field from a step's output). Kept intentionally small
and total: any type mismatch or unknown operator returns False rather than
raising, so a malformed rule can never crash execution — it simply doesn't
match (and should have been caught at rule-validation time).

Supported operators are deliberately limited to what banking thresholds need.
This function is generic over the "facts" — data outputs today, identity
attributes for RBAC later.
"""


class RuleOperator:
    EQ = "=="
    NE = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    IN = "in"
    NOT_IN = "not_in"


SUPPORTED_OPERATORS = {
    RuleOperator.EQ,
    RuleOperator.NE,
    RuleOperator.GT,
    RuleOperator.GTE,
    RuleOperator.LT,
    RuleOperator.LTE,
    RuleOperator.IN,
    RuleOperator.NOT_IN,
}

_NUMERIC_OPS = {RuleOperator.GT, RuleOperator.GTE, RuleOperator.LT, RuleOperator.LTE}


def _as_number(value):
    """Coerce numeric strings to float; return None if not numeric."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def evaluate_condition(op: str, actual, expected) -> bool:
    """Evaluate ``actual <op> expected``. Total: never raises, returns bool.

    Args:
        op: one of SUPPORTED_OPERATORS.
        actual: the value read from a step output (may be None if missing).
        expected: the value declared in the rule.
    """
    if op not in SUPPORTED_OPERATORS:
        return False

    if op == RuleOperator.EQ:
        return actual == expected
    if op == RuleOperator.NE:
        return actual != expected

    if op == RuleOperator.IN:
        try:
            return actual in expected
        except TypeError:
            return False
    if op == RuleOperator.NOT_IN:
        try:
            return actual not in expected
        except TypeError:
            return False

    # Ordered comparisons — require both sides to be numeric.
    if op in _NUMERIC_OPS:
        a = _as_number(actual)
        e = _as_number(expected)
        if a is None or e is None:
            return False
        if op == RuleOperator.GT:
            return a > e
        if op == RuleOperator.GTE:
            return a >= e
        if op == RuleOperator.LT:
            return a < e
        if op == RuleOperator.LTE:
            return a <= e

    return False
