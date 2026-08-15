"""Unit tests for deterministic business-rule threshold conflict detection."""

from app.workflow.rule_conflicts import (
    detect_rule_conflicts,
    extract_amounts,
    subject_key,
)


# ── extract_amounts ────────────────────────────────────────────────────────────

def test_extract_lakh_and_crore():
    assert extract_amounts("above ₹5 lakh") == [500_000.0]
    assert extract_amounts("over 10 lakh") == [1_000_000.0]
    assert extract_amounts("exceeds 2 crore") == [20_000_000.0]


def test_extract_currency_grouped_number():
    assert extract_amounts("above ₹5,00,000") == [500_000.0]


def test_bare_small_number_ignored():
    # "3 approvals" is not a monetary threshold
    assert extract_amounts("requires 3 approvals") == []


# ── subject_key ─────────────────────────────────────────────────────────────────

def test_subject_key_ignores_amounts():
    a = subject_key("Approval required above ₹5 lakh.")
    b = subject_key("Approval required above ₹10 lakh.")
    assert a == b
    assert "approval" in a and "above" in a


# ── detect_rule_conflicts ─────────────────────────────────────────────────────

def _rule(text, doc):
    return {"rule": text, "source_document": doc}


def test_threshold_conflict_detected():
    rules = [
        _rule("Approval required above ₹5 lakh.", "brd_a.pdf"),
        _rule("Approval required above ₹10 lakh.", "brd_b.pdf"),
    ]
    conflicts = detect_rule_conflicts(rules)
    assert len(conflicts) == 1
    c = conflicts[0]
    assert c["type"] == "threshold_conflict"
    assert len(c["rules"]) == 2
    assert {"brd_a.pdf", "brd_b.pdf"} == {r["source_document"] for r in c["rules"]}


def test_same_threshold_is_not_a_conflict():
    rules = [
        _rule("Approval required above ₹5 lakh.", "brd_a.pdf"),
        _rule("Approval required above ₹5 lakh.", "brd_b.pdf"),
    ]
    assert detect_rule_conflicts(rules) == []


def test_different_subjects_do_not_conflict():
    rules = [
        _rule("Approval required above ₹5 lakh.", "brd_a.pdf"),
        _rule("Manual review required below ₹1 lakh.", "brd_b.pdf"),
    ]
    assert detect_rule_conflicts(rules) == []


def test_rule_without_threshold_word_ignored():
    rules = [
        _rule("The applicant provides ₹5 lakh as collateral.", "brd_a.pdf"),
        _rule("The applicant provides ₹10 lakh as collateral.", "brd_b.pdf"),
    ]
    # No threshold indicator ("above"/"exceed"/...) → not flagged.
    assert detect_rule_conflicts(rules) == []


def test_no_conflict_with_single_rule():
    assert detect_rule_conflicts([_rule("Approval required above ₹5 lakh.", "a.pdf")]) == []
