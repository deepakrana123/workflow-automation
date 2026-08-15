"""Unit tests for the deterministic workflow explainer (pure builder)."""

from app.workflow.workflow_explainer import build_explanation, _topological_order


_COMPILED = {
    "trigger": {"event_type": "loan_application_received"},
    "steps": [
        {"id": "a", "action": "run_cibil_check", "depends_on": []},
        {"id": "b", "action": "assess_creditworthiness", "depends_on": ["a"]},
        {"id": "c", "action": "approve_loan", "depends_on": ["b"]},
    ],
}

_ACTION_META = {
    "run_cibil_check": {"display_name": "Run CIBIL Check", "description": "Fetches the credit bureau score."},
    "assess_creditworthiness": {"display_name": "Assess Creditworthiness", "description": "Evaluates risk."},
    "approve_loan": {"display_name": "Approve Loan", "description": "Marks the loan approved."},
}

_TRIGGER_META = {"display_name": "Loan Application Received", "description": "A new loan application arrives."}


def test_summary_mentions_trigger_and_step_count():
    exp = build_explanation(_COMPILED, _ACTION_META, _TRIGGER_META, domain="finance")
    assert "loan_application_received" in exp["summary"]
    assert "3 step" in exp["summary"]
    assert "finance" in exp["summary"]


def test_execution_order_is_topological():
    exp = build_explanation(_COMPILED, _ACTION_META, _TRIGGER_META)
    assert exp["execution_order"] == ["a", "b", "c"]


def test_first_step_runs_at_start():
    exp = build_explanation(_COMPILED, _ACTION_META, _TRIGGER_META)
    first = exp["steps"][0]
    assert first["id"] == "a"
    assert "start" in first["explanation"].lower()
    assert "credit bureau" in first["explanation"]  # catalog description appended


def test_dependent_step_mentions_dependency():
    exp = build_explanation(_COMPILED, _ACTION_META, _TRIGGER_META)
    step_b = next(s for s in exp["steps"] if s["id"] == "b")
    assert "a" in step_b["explanation"]
    assert step_b["display_name"] == "Assess Creditworthiness"


def test_trigger_description_included():
    exp = build_explanation(_COMPILED, _ACTION_META, _TRIGGER_META)
    assert exp["trigger"]["event"] == "loan_application_received"
    assert exp["trigger"]["description"] == "A new loan application arrives."


def test_missing_catalog_meta_falls_back_to_action_name():
    exp = build_explanation(_COMPILED, {}, None)
    # No catalog metadata -> display_name defaults to the raw action name.
    assert exp["steps"][0]["display_name"] == "run_cibil_check"
    assert exp["steps"][0]["description"] == ""


def test_topological_order_handles_cycle_without_raising():
    cyclic = [
        {"id": "x", "action": "ax", "depends_on": ["y"]},
        {"id": "y", "action": "ay", "depends_on": ["x"]},
    ]
    order = _topological_order(cyclic)
    assert set(order) == {"x", "y"}  # returns all ids, doesn't hang or raise


def test_no_trigger_still_produces_summary():
    compiled = {"trigger": {}, "steps": [{"id": "a", "action": "approve_loan", "depends_on": []}]}
    exp = build_explanation(compiled, _ACTION_META, None, domain="finance")
    assert "1 step" in exp["summary"]
