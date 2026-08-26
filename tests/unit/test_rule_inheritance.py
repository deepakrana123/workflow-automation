"""Unit tests for multi-level rule restriction enforcement."""

from app.rbac.rule_inheritance import is_more_restrictive, validate_new_rule


# ── is_more_restrictive — lower bound (>=) ────────────────────────────────────

def test_higher_lower_bound_is_more_restrictive():
    # Global: loan_amount >= 500000
    # Branch: loan_amount >= 750000  → more restrictive (higher minimum)
    assert is_more_restrictive(
        {"field": "loan_amount", "op": ">=", "value": 750000},
        {"field": "loan_amount", "op": ">=", "value": 500000},
    ) is True


def test_lower_lower_bound_relaxes_global():
    # Branch tries to allow loan_amount >= 300000 when global says >= 500000
    assert is_more_restrictive(
        {"field": "loan_amount", "op": ">=", "value": 300000},
        {"field": "loan_amount", "op": ">=", "value": 500000},
    ) is False


def test_equal_threshold_is_accepted():
    assert is_more_restrictive(
        {"field": "loan_amount", "op": ">=", "value": 500000},
        {"field": "loan_amount", "op": ">=", "value": 500000},
    ) is True


# ── is_more_restrictive — upper bound (<=) ────────────────────────────────────

def test_lower_upper_bound_is_more_restrictive():
    # Global: transaction_amount <= 1000000
    # Branch: transaction_amount <= 500000  → more restrictive (lower cap)
    assert is_more_restrictive(
        {"field": "transaction_amount", "op": "<=", "value": 500000},
        {"field": "transaction_amount", "op": "<=", "value": 1000000},
    ) is True


def test_higher_upper_bound_relaxes():
    assert is_more_restrictive(
        {"field": "transaction_amount", "op": "<=", "value": 2000000},
        {"field": "transaction_amount", "op": "<=", "value": 1000000},
    ) is False


# ── is_more_restrictive — in / not_in ────────────────────────────────────────

def test_subset_is_more_restrictive_for_in():
    # Global allows ["A", "B", "C"]; branch allows only ["A"] → more restrictive
    assert is_more_restrictive(
        {"field": "risk_category", "op": "in", "value": ["A"]},
        {"field": "risk_category", "op": "in", "value": ["A", "B", "C"]},
    ) is True


def test_superset_relaxes_in():
    assert is_more_restrictive(
        {"field": "risk_category", "op": "in", "value": ["A", "B", "C", "D"]},
        {"field": "risk_category", "op": "in", "value": ["A", "B", "C"]},
    ) is False


# ── is_more_restrictive — different fields / ops ──────────────────────────────

def test_different_field_is_not_a_conflict():
    assert is_more_restrictive(
        {"field": "loan_amount", "op": ">=", "value": 100},
        {"field": "credit_score", "op": ">=", "value": 750},
    ) is True


def test_different_op_is_not_a_conflict():
    assert is_more_restrictive(
        {"field": "loan_amount", "op": "<=", "value": 500000},
        {"field": "loan_amount", "op": ">=", "value": 500000},
    ) is True


# ── is_more_restrictive — equality ───────────────────────────────────────────

def test_same_equality_value_accepted():
    assert is_more_restrictive(
        {"field": "status", "op": "==", "value": "APPROVED"},
        {"field": "status", "op": "==", "value": "APPROVED"},
    ) is True


def test_different_equality_value_rejected():
    assert is_more_restrictive(
        {"field": "status", "op": "==", "value": "PENDING"},
        {"field": "status", "op": "==", "value": "APPROVED"},
    ) is False


# ── is_more_restrictive — type-safety ────────────────────────────────────────

def test_non_numeric_value_for_numeric_op_returns_false():
    assert is_more_restrictive(
        {"field": "amount", "op": ">=", "value": "not-a-number"},
        {"field": "amount", "op": ">=", "value": 100},
    ) is False


def test_none_value_returns_false():
    assert is_more_restrictive(
        {"field": "amount", "op": ">=", "value": None},
        {"field": "amount", "op": ">=", "value": 100},
    ) is False
