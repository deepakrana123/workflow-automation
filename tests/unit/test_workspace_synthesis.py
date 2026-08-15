"""Unit tests for the deterministic multi-BRD workspace synthesis builder."""

from app.workflow.workspace_synthesis import build_workspace_synthesis


def _brd(wk_id, doc, actions, triggers=None, rules=None):
    return {
        "workflow_knowledge_id": wk_id,
        "workflow_name": f"wf-{wk_id}",
        "source_document": doc,
        "actions": actions,
        "triggers": triggers or [],
        "business_rules": rules or [],
    }


def _action(canonical_id, name, term, clause, confidence=0.9):
    return {
        "canonical_id": canonical_id,
        "canonical_name": name,
        "display_name": name.replace("_", " ").title(),
        "term": term,
        "clause": clause,
        "confidence": confidence,
        "similarity": 0.8,
        "status": "MAPPED",
    }


def test_same_action_across_brds_is_deduplicated():
    items = [
        _brd(1, "brd1.pdf", [_action(10, "run_cibil_check", "cibil check", "Check CIBIL.")]),
        _brd(2, "brd2.pdf", [_action(10, "run_cibil_check", "credit check", "Verify credit.")]),
    ]
    result = build_workspace_synthesis(items)
    # One canonical action, contributed by two BRDs.
    assert len(result["actions"]) == 1
    action = result["actions"][0]
    assert action["action"] == "run_cibil_check"
    assert action["contributed_by"] == 2
    assert len(action["sources"]) == 2


def test_distinct_actions_are_kept_separate():
    items = [
        _brd(1, "brd1.pdf", [
            _action(10, "run_cibil_check", "cibil", "c"),
            _action(11, "approve_loan", "approve", "a"),
        ]),
    ]
    result = build_workspace_synthesis(items)
    assert len(result["actions"]) == 2


def test_unresolved_action_is_flagged():
    items = [
        _brd(1, "brd1.pdf", [
            {"canonical_id": None, "canonical_name": None, "display_name": None,
             "term": "do magic", "clause": "The system shall do magic.",
             "confidence": None, "similarity": None, "status": "UNMAPPED"},
        ]),
    ]
    result = build_workspace_synthesis(items)
    assert len(result["actions"]) == 0
    assert len(result["unresolved_actions"]) == 1
    assert any(f["type"] == "unresolved_action" for f in result["review_flags"])


def test_low_confidence_action_is_flagged():
    items = [_brd(1, "brd1.pdf", [_action(10, "run_cibil_check", "x", "y", confidence=0.3)])]
    result = build_workspace_synthesis(items)
    flags = [f for f in result["review_flags"] if f["type"] == "low_confidence"]
    assert len(flags) == 1
    assert flags[0]["action"] == "run_cibil_check"


def test_min_confidence_is_the_lowest_across_sources():
    items = [
        _brd(1, "brd1.pdf", [_action(10, "run_cibil_check", "x", "y", confidence=0.9)]),
        _brd(2, "brd2.pdf", [_action(10, "run_cibil_check", "x", "y", confidence=0.6)]),
    ]
    result = build_workspace_synthesis(items)
    assert result["actions"][0]["min_confidence"] == 0.6


def test_business_rules_collected_with_source():
    items = [_brd(1, "brd1.pdf", [], rules=["Approve if score > 750."])]
    result = build_workspace_synthesis(items)
    assert result["business_rules"][0]["rule"] == "Approve if score > 750."
    assert result["business_rules"][0]["source_document"] == "brd1.pdf"


def test_brd_count_and_documents():
    items = [
        _brd(1, "a.pdf", [_action(10, "x", "t", "c")]),
        _brd(2, "b.pdf", [_action(11, "y", "t", "c")]),
    ]
    result = build_workspace_synthesis(items)
    assert result["brd_count"] == 2
    assert {d["source_document"] for d in result["documents"]} == {"a.pdf", "b.pdf"}


def test_triggers_deduplicated_by_canonical():
    items = [
        _brd(1, "a.pdf", [], triggers=[{"canonical_id": 5, "canonical_name": "loan_received", "term": "app received", "clause": "c"}]),
        _brd(2, "b.pdf", [], triggers=[{"canonical_id": 5, "canonical_name": "loan_received", "term": "new loan", "clause": "c"}]),
    ]
    result = build_workspace_synthesis(items)
    assert len(result["triggers"]) == 1
    assert len(result["triggers"][0]["sources"]) == 2
