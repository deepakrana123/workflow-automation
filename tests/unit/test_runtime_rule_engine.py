"""
Unit tests for RuntimeRuleEngine — pure logic layer.

Uses mocked DB and pre-built BusinessRuleDefinition fakes
so no database connection is needed.
"""
from unittest.mock import MagicMock, patch
from app.runtime.context import RuleEvaluationContext


# ── Fake rule builder ─────────────────────────────────────────────────────────

def _fake_rule(id_, field, op, value, description="test rule",
               workspace_id=1, locked=False, active=True):
    r = MagicMock()
    r.id = id_
    r.field = field
    r.op = op
    r.value = value
    r.description = description
    r.scope_workspace_id = workspace_id
    r.locked = locked
    r.active = active
    r.allowed_roles = []
    r.is_evaluable.return_value = (field is not None and op is not None and value is not None)
    return r


def _make_engine(inherited_rules=None, step_rules=None):
    """Build RuntimeRuleEngine with mocked DB."""
    from app.runtime.rule_engine import RuntimeRuleEngine

    engine = RuntimeRuleEngine.__new__(RuntimeRuleEngine)
    engine._db = MagicMock()

    # Patch resolve_effective_rules to return controlled rules
    with patch("app.runtime.rule_engine.resolve_effective_rules",
               return_value=inherited_rules or []):
        pass  # just setting up; actual patch applied in tests

    engine._inherited_rules_override = inherited_rules or []
    engine._step_rules_override = step_rules or []

    # Patch internal helpers
    engine._get_step_rules = MagicMock(return_value=step_rules or [])
    engine._check_step_roles = MagicMock(return_value=None)

    return engine


def _ctx(**kwargs):
    defaults = dict(user_id="u1", workspace_id=1)
    defaults.update(kwargs)
    return RuleEvaluationContext(**defaults)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_no_rules_always_passes():
    from app.runtime.rule_engine import RuntimeRuleEngine
    engine = _make_engine()

    with patch("app.runtime.rule_engine.resolve_effective_rules", return_value=[]):
        result = engine.evaluate(_ctx())

    assert result.allowed is True
    assert result.failed_rules == []


def test_passing_inherited_rule_allows():
    from app.runtime.rule_engine import RuntimeRuleEngine
    engine = _make_engine()
    rule = _fake_rule(1, "loan_amount", ">=", 100000)

    with patch("app.runtime.rule_engine.resolve_effective_rules", return_value=[rule]):
        result = engine.evaluate(_ctx(
            request_data={"loan_amount": 500000}
        ))

    assert result.allowed is True
    assert len(result.decisions) == 1


def test_failing_inherited_rule_blocks():
    from app.runtime.rule_engine import RuntimeRuleEngine
    engine = _make_engine()
    rule = _fake_rule(1, "loan_amount", ">=", 500000, description="Min loan 5L")

    with patch("app.runtime.rule_engine.resolve_effective_rules", return_value=[rule]):
        result = engine.evaluate(_ctx(
            request_data={"loan_amount": 100000}
        ))

    assert result.allowed is False
    assert len(result.failed_rules) == 1
    assert "RULE_FAILED" in result.failed_rules[0]["code"]


def test_first_failing_rule_stops_evaluation():
    from app.runtime.rule_engine import RuntimeRuleEngine
    engine = _make_engine()

    rule_a = _fake_rule(1, "loan_amount", ">=", 500000, description="rule A")
    rule_b = _fake_rule(2, "credit_score", ">=", 700, description="rule B")

    with patch("app.runtime.rule_engine.resolve_effective_rules",
               return_value=[rule_a, rule_b]):
        result = engine.evaluate(_ctx(
            request_data={"loan_amount": 100, "credit_score": 800}
        ))

    assert result.allowed is False
    # Only rule A evaluated (rule B never reached)
    assert len(result.decisions) == 1
    assert result.decisions[0]["description"] == "rule A"


def test_description_only_rule_passes_without_evaluation():
    from app.runtime.rule_engine import RuntimeRuleEngine
    engine = _make_engine()

    rule = _fake_rule(1, None, None, None, description="Policy: document required")
    rule.is_evaluable.return_value = False

    with patch("app.runtime.rule_engine.resolve_effective_rules", return_value=[rule]):
        result = engine.evaluate(_ctx())

    assert result.allowed is True
    assert result.decisions[0]["evaluable"] is False
    assert result.decisions[0]["result"] is True


def test_step_rules_evaluated_after_inherited():
    from app.runtime.rule_engine import RuntimeRuleEngine
    engine = _make_engine()

    inherited = [_fake_rule(1, "global_cap", "<=", 10_000_000)]
    step_rule  = {"field": "loan_amount", "op": ">=", "value": 50000, "description": "step rule"}
    engine._get_step_rules = MagicMock(return_value=[step_rule])

    with patch("app.runtime.rule_engine.resolve_effective_rules", return_value=inherited):
        result = engine.evaluate(_ctx(
            workflow_id=1, step_id="s1",
            request_data={"global_cap": 5_000_000, "loan_amount": 100_000},
        ))

    assert result.allowed is True
    assert len(result.decisions) == 2  # one inherited + one step


def test_step_rule_failure_blocks_execution():
    from app.runtime.rule_engine import RuntimeRuleEngine
    engine = _make_engine()

    step_rule = {"field": "loan_amount", "op": ">=", "value": 500000, "description": "min loan"}
    engine._get_step_rules = MagicMock(return_value=[step_rule])

    with patch("app.runtime.rule_engine.resolve_effective_rules", return_value=[]):
        result = engine.evaluate(_ctx(
            workflow_id=1, step_id="s1",
            request_data={"loan_amount": 1000},
        ))

    assert result.allowed is False
    assert result.failed_rules[0]["code"] == "STEP_RULE_FAILED:loan_amount:>="


def test_missing_context_field_blocks_rule():
    """If the rule's field is not present in facts, actual=None → rule fails."""
    from app.runtime.rule_engine import RuntimeRuleEngine
    engine = _make_engine()

    rule = _fake_rule(1, "loan_amount", ">=", 500000)
    with patch("app.runtime.rule_engine.resolve_effective_rules", return_value=[rule]):
        result = engine.evaluate(_ctx())  # no request_data

    assert result.allowed is False


def test_rule_evaluation_result_has_structured_output():
    from app.runtime.rule_engine import RuntimeRuleEngine
    engine = _make_engine()
    rule = _fake_rule(1, "amount", ">=", 100, description="amount check")

    with patch("app.runtime.rule_engine.resolve_effective_rules", return_value=[rule]):
        result = engine.evaluate(_ctx(request_data={"amount": 200}))

    d = result.to_dict()
    assert "allowed" in d
    assert "decisions" in d
    assert "failed_rules" in d
    assert "warnings" in d
    assert d["allowed"] is True


def test_exception_in_rule_engine_fails_closed():
    from app.runtime.rule_engine import RuntimeRuleEngine
    engine = _make_engine()

    with patch("app.runtime.rule_engine.resolve_effective_rules",
               side_effect=RuntimeError("DB down")):
        result = engine.evaluate(_ctx())

    # Fail closed — exception → denied
    assert result.allowed is False
    assert result.failed_rules[0]["code"] == "INTERNAL_ERROR"
