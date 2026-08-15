"""Unit tests for the rule engine core: evaluator, routing, skip cascade."""

from app.execution.rules.evaluator import evaluate_condition, RuleOperator
from app.execution.rules.routing import (
    resolve_activated_children,
    resolve_skipped_steps,
)
from app.execution.runtime.dag_scheduler import get_ready_steps


# ── evaluate_condition ────────────────────────────────────────────────────────

def test_numeric_operators():
    assert evaluate_condition(">=", 750, 750) is True
    assert evaluate_condition(">", 800, 750) is True
    assert evaluate_condition("<", 700, 750) is True
    assert evaluate_condition("<=", 750, 750) is True
    assert evaluate_condition(">", 700, 750) is False


def test_numeric_operators_coerce_string_numbers():
    assert evaluate_condition(">=", "780", 750) is True
    assert evaluate_condition("<", "700", "750") is True


def test_equality_operators():
    assert evaluate_condition("==", "APPROVED", "APPROVED") is True
    assert evaluate_condition("!=", "APPROVED", "REJECTED") is True
    assert evaluate_condition("==", 5, 5) is True


def test_in_operators():
    assert evaluate_condition("in", "HIGH", ["HIGH", "MEDIUM"]) is True
    assert evaluate_condition("not_in", "LOW", ["HIGH", "MEDIUM"]) is True
    assert evaluate_condition("in", "LOW", ["HIGH"]) is False


def test_unknown_operator_is_false():
    assert evaluate_condition("~=", 1, 1) is False


def test_non_numeric_ordered_comparison_is_false_not_raise():
    assert evaluate_condition(">", "abc", 750) is False
    assert evaluate_condition(">", None, 750) is False


def test_booleans_not_treated_as_numbers():
    # True must not sneak into numeric comparison as 1.
    assert evaluate_condition(">", True, 0) is False


# ── resolve_activated_children ────────────────────────────────────────────────

_ROUTING = {
    "field": "credit_score",
    "branches": [
        {"when": {"op": ">=", "value": 750}, "activate": ["approve"]},
        {"when": {"op": "<", "value": 750}, "activate": ["reject"]},
    ],
    "default": ["manual_review"],
}


def test_first_matching_branch_wins():
    assert resolve_activated_children(_ROUTING, {"credit_score": 800}) == ["approve"]
    assert resolve_activated_children(_ROUTING, {"credit_score": 600}) == ["reject"]


def test_default_when_no_branch_matches():
    routing = {
        "field": "risk",
        "branches": [{"when": {"op": "==", "value": "LOW"}, "activate": ["a"]}],
        "default": ["manual_review"],
    }
    assert resolve_activated_children(routing, {"risk": "HIGH"}) == ["manual_review"]


def test_missing_field_falls_to_default():
    assert resolve_activated_children(_ROUTING, {}) == ["manual_review"]


def test_empty_routing_activates_nothing():
    assert resolve_activated_children({}, {"credit_score": 800}) == []


# ── resolve_skipped_steps ─────────────────────────────────────────────────────

_STEPS = [
    {"id": "cibil", "depends_on": []},
    {"id": "approve", "depends_on": ["cibil"]},
    {"id": "reject", "depends_on": ["cibil"]},
    {"id": "disburse", "depends_on": ["approve"]},   # descendant of approve
    {"id": "notify_reject", "depends_on": ["reject"]},  # descendant of reject
]


def test_non_activated_child_is_skipped():
    skipped = resolve_skipped_steps(_STEPS, "cibil", ["approve"])
    assert "reject" in skipped
    assert "approve" not in skipped


def test_skip_cascades_to_descendants():
    skipped = resolve_skipped_steps(_STEPS, "cibil", ["approve"])
    # reject not taken -> its descendant notify_reject also skipped
    assert "notify_reject" in skipped
    # approve taken -> disburse must NOT be skipped
    assert "disburse" not in skipped


def test_activating_reject_skips_approve_subtree():
    skipped = resolve_skipped_steps(_STEPS, "cibil", ["reject"])
    assert {"approve", "disburse"} <= skipped
    assert "reject" not in skipped
    assert "notify_reject" not in skipped


# ── scheduler skipped-awareness ───────────────────────────────────────────────

def test_get_ready_steps_excludes_skipped():
    ready = get_ready_steps(
        _STEPS,
        completed_steps={"cibil"},
        failed_steps=set(),
        skipped_steps={"reject", "notify_reject"},
    )
    ids = {s["id"] for s in ready}
    assert "approve" in ids       # activated branch is ready
    assert "reject" not in ids    # skipped branch never scheduled


def test_skipped_dependency_does_not_make_child_ready():
    # disburse depends on approve; approve not completed -> disburse not ready
    ready = get_ready_steps(
        _STEPS,
        completed_steps={"cibil"},
        failed_steps=set(),
        skipped_steps={"reject"},
    )
    assert all(s["id"] != "disburse" for s in ready)
