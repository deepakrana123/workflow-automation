"""Unit tests for StepRuleEvaluator — the execution boundary gate."""

from app.execution.rules.step_rule_evaluator import (
    evaluate_step_rules,
    build_metadata_entry,
    EvalResult,
)


def _rule(field, op, value, description="test rule", roles=None, scope=None):
    return {
        "field": field,
        "op": op,
        "value": value,
        "description": description,
        "allowed_roles": roles or [],
        "scope_workspace_id": scope,
    }


def _step(rules=None):
    return {"id": "s1", "action": "approve_loan", "business_rules": rules or []}


# ── Basic pass / block ────────────────────────────────────────────────────────

def test_step_with_no_rules_passes():
    result = evaluate_step_rules(_step(), context_outputs={})
    assert result.passed is True
    assert result.blocking_rule is None
    assert result.evaluations == []


def test_rule_satisfied_passes():
    step = _step([_rule("loan_amount", ">=", 500000)])
    result = evaluate_step_rules(step, {"loan_amount": 600000})
    assert result.passed is True


def test_rule_not_satisfied_blocks():
    step = _step([_rule("loan_amount", ">=", 500000)])
    result = evaluate_step_rules(step, {"loan_amount": 300000})
    assert result.passed is False
    assert result.blocking_rule is not None
    assert result.blocking_rule.field == "loan_amount"


def test_first_failing_rule_stops_evaluation():
    step = _step([
        _rule("loan_amount", ">=", 500000, "rule A"),
        _rule("credit_score", ">=", 700, "rule B"),
    ])
    # loan_amount fails → rule B should never be evaluated
    result = evaluate_step_rules(step, {"loan_amount": 100000, "credit_score": 800})
    assert result.passed is False
    assert result.blocking_rule.rule_description == "rule A"
    assert len(result.evaluations) == 1   # stopped at first failure


def test_all_rules_must_pass():
    step = _step([
        _rule("loan_amount", ">=", 500000),
        _rule("credit_score", ">=", 700),
    ])
    result = evaluate_step_rules(step, {"loan_amount": 600000, "credit_score": 750})
    assert result.passed is True
    assert len(result.evaluations) == 2


# ── Missing field in context ──────────────────────────────────────────────────

def test_missing_field_evaluates_to_false():
    step = _step([_rule("loan_amount", ">=", 500000)])
    # context_outputs does not contain loan_amount → actual = None → blocked
    result = evaluate_step_rules(step, {})
    assert result.passed is False


# ── Description-only rule (no field) always passes ───────────────────────────

def test_description_only_rule_always_passes():
    step = _step([{"description": "Policy note: document must be stamped", "allowed_roles": []}])
    result = evaluate_step_rules(step, {})
    assert result.passed is True


# ── Inherited rules ──────────────────────────────────────────────────────────

def test_inherited_rule_evaluated_before_step_rules():
    inherited = [_rule("global_limit", "<=", 10_000_000, "global cap", scope=1)]
    step      = _step([_rule("loan_amount", ">=", 500000)])

    # Global cap violated → should block on inherited rule first
    result = evaluate_step_rules(
        step,
        {"global_limit": 20_000_000, "loan_amount": 600000},
        inherited_rules=inherited,
    )
    assert result.passed is False
    assert result.blocking_rule.scope_workspace_id == 1


def test_passing_inherited_rule_proceeds_to_step_rules():
    inherited = [_rule("global_limit", "<=", 10_000_000, scope=1)]
    step      = _step([_rule("loan_amount", ">=", 500000)])

    result = evaluate_step_rules(
        step,
        {"global_limit": 5_000_000, "loan_amount": 600000},
        inherited_rules=inherited,
    )
    assert result.passed is True
    assert len(result.evaluations) == 2


# ── build_metadata_entry ──────────────────────────────────────────────────────

def test_metadata_entry_on_pass():
    step   = _step([_rule("loan_amount", ">=", 500000)])
    result = evaluate_step_rules(step, {"loan_amount": 600000})
    meta   = build_metadata_entry(result)

    assert meta["passed"] is True
    assert meta["total"] == 1
    assert meta["passed_count"] == 1
    assert meta["failed_count"] == 0
    assert meta["blocking_rule"] is None


def test_metadata_entry_on_block():
    step   = _step([_rule("loan_amount", ">=", 500000, "Loan policy")])
    result = evaluate_step_rules(step, {"loan_amount": 100000})
    meta   = build_metadata_entry(result)

    assert meta["passed"] is False
    assert meta["failed_count"] == 1
    assert meta["blocking_rule"]["field"] == "loan_amount"
    assert meta["blocking_rule"]["actual"] == 100000
    assert meta["blocking_rule"]["description"] == "Loan policy"


def test_metadata_summary_counts():
    step = _step([
        _rule("a", ">=", 1),
        _rule("b", ">=", 1),
        _rule("c", ">=", 1),
    ])
    result = evaluate_step_rules(
        step,
        {"a": 5, "b": 5, "c": 5},
    )
    meta = build_metadata_entry(result)
    assert meta["total"] == 3
    assert meta["passed_count"] == 3
    assert meta["failed_count"] == 0


# ── Operator coverage ─────────────────────────────────────────────────────────

def test_in_operator():
    step = _step([_rule("risk", "in", ["LOW", "MEDIUM"])])
    assert evaluate_step_rules(step, {"risk": "LOW"}).passed is True
    assert evaluate_step_rules(step, {"risk": "HIGH"}).passed is False


def test_not_in_operator():
    step = _step([_rule("country", "not_in", ["BLACKLISTED"])])
    assert evaluate_step_rules(step, {"country": "IN"}).passed is True
    assert evaluate_step_rules(step, {"country": "BLACKLISTED"}).passed is False


def test_equality_operator():
    step = _step([_rule("status", "==", "APPROVED")])
    assert evaluate_step_rules(step, {"status": "APPROVED"}).passed is True
    assert evaluate_step_rules(step, {"status": "REJECTED"}).passed is False
