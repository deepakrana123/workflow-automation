"""Unit tests for RuleExtractionService helpers (pure functions)."""

from app.rbac.rule_extractor import (
    map_actor_to_role,
    _infer_operator,
    _infer_field,
)


# ── map_actor_to_role ─────────────────────────────────────────────────────────

def test_branch_manager_maps_correctly():
    assert map_actor_to_role("Branch Manager") == "branch_manager"
    assert map_actor_to_role("branch manager") == "branch_manager"
    assert map_actor_to_role("Head of Branch") == "branch_manager"


def test_zone_manager_maps():
    assert map_actor_to_role("Zonal Head") == "zone_manager"
    assert map_actor_to_role("Zone Manager") == "zone_manager"


def test_region_manager_maps():
    assert map_actor_to_role("Regional Head") == "region_manager"
    assert map_actor_to_role("Region Manager") == "region_manager"


def test_loan_officer_maps_to_branch_officer():
    assert map_actor_to_role("Loan Officer") == "branch_officer"
    assert map_actor_to_role("Credit Officer") == "branch_officer"


def test_auditor_maps():
    assert map_actor_to_role("Auditor") == "auditor"
    assert map_actor_to_role("Compliance Team") == "auditor"


def test_unknown_actor_maps_to_read_only():
    assert map_actor_to_role("Random Person") == "read_only"
    assert map_actor_to_role("") == "read_only"
    assert map_actor_to_role(None) == "read_only"


# ── _infer_operator ───────────────────────────────────────────────────────────

def test_above_infers_gte():
    assert _infer_operator("Approval required above ₹5 lakh") == ">="


def test_below_infers_lte():
    assert _infer_operator("Waiver allowed below ₹10,000") == "<="


def test_exceeds_infers_gte():
    assert _infer_operator("Escalate when loan exceeds ₹25 lakh") == ">="


def test_default_operator_is_gte():
    assert _infer_operator("Some rule with no direction word ₹100") == ">="


# ── _infer_field ──────────────────────────────────────────────────────────────

def test_loan_amount_field():
    assert _infer_field("Loan amount above ₹5 lakh") == "loan_amount"
    assert _infer_field("Disbursement above ₹10 lakh") == "loan_amount"


def test_credit_score_field():
    assert _infer_field("CIBIL score must be above 700") == "credit_score"


def test_unknown_field_returns_none():
    assert _infer_field("Some unknown metric above 100") is None


def test_transaction_amount_field():
    assert _infer_field("Transaction above ₹1 lakh requires approval") == "transaction_amount"
