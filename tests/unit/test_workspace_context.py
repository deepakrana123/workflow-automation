"""Unit tests for the read-only workspace context builders.

Pure functions only — no DB. Mirrors test_workspace_synthesis.py style.
"""

from app.workflow.workspace_context import build_document_view, build_overview


# ── build_overview ────────────────────────────────────────────────────────────

def _workspace(active=True):
    return {
        "id": 1,
        "name": "personal_loan_approval",
        "display_name": "Personal Loan Approval",
        "organization_name": "Acme Bank",
        "description": "Handles personal loan applications end to end.",
        "active": active,
    }


def _synthesis(actions=0, unresolved=0, triggers=0, rules=0, flags=0, brds=0):
    return {
        "brd_count": brds,
        "actions": [{"canonical_id": i} for i in range(actions)],
        "unresolved_actions": [{} for _ in range(unresolved)],
        "triggers": [{} for _ in range(triggers)],
        "business_rules": [{} for _ in range(rules)],
        "review_flags": [{} for _ in range(flags)],
    }


def test_overview_maps_counts_from_synthesis():
    result = build_overview(
        workspace=_workspace(),
        synthesis=_synthesis(actions=12, unresolved=2, triggers=4, rules=9, flags=1, brds=3),
        domain="loan_servicing",
    )
    assert result["display_name"] == "Personal Loan Approval"
    assert result["domain"] == "loan_servicing"
    assert result["summary"] == "Handles personal loan applications end to end."
    assert result["status"] == "active"
    assert result["brd_count"] == 3
    assert result["action_count"] == 12
    assert result["unresolved_action_count"] == 2
    assert result["trigger_count"] == 4
    assert result["business_rule_count"] == 9
    assert result["review_flag_count"] == 1


def test_overview_defaults_workflow_and_file_counts_to_zero():
    result = build_overview(workspace=_workspace(), synthesis=_synthesis())
    assert result["workflow_count"] == 0
    assert result["generated_file_count"] == 0


def test_overview_reflects_workflow_count():
    result = build_overview(workspace=_workspace(), synthesis=_synthesis(), workflow_count=3)
    assert result["workflow_count"] == 3


def test_overview_inactive_status():
    result = build_overview(workspace=_workspace(active=False), synthesis=_synthesis())
    assert result["status"] == "inactive"


def test_overview_handles_empty_synthesis():
    result = build_overview(workspace=_workspace(), synthesis={})
    assert result["action_count"] == 0
    assert result["brd_count"] == 0
    assert result["domain"] is None


# ── build_document_view ───────────────────────────────────────────────────────

def test_document_all_actions_mapped():
    docs = build_document_view([
        {"workflow_knowledge_id": 1, "workflow_name": "wf", "source_document": "brd1.pdf",
         "created_at": None, "action_total": 3, "action_mapped": 3, "trigger_total": 1, "rule_total": 2},
    ])
    assert docs[0]["mapping_status"] == "mapped"
    assert docs[0]["extraction_status"] == "extracted"
    assert docs[0]["action_count"] == 3
    assert docs[0]["business_rule_count"] == 2
    assert docs[0]["name"] == "brd1.pdf"


def test_document_partial_mapping():
    docs = build_document_view([
        {"workflow_knowledge_id": 1, "source_document": "brd1.pdf",
         "action_total": 3, "action_mapped": 1},
    ])
    assert docs[0]["mapping_status"] == "partial"


def test_document_no_actions_mapped():
    docs = build_document_view([
        {"workflow_knowledge_id": 1, "source_document": "brd1.pdf",
         "action_total": 2, "action_mapped": 0, "rule_total": 1},
    ])
    assert docs[0]["mapping_status"] == "unmapped"
    assert docs[0]["extraction_status"] == "extracted"  # rules were extracted


def test_document_nothing_extracted():
    docs = build_document_view([
        {"workflow_knowledge_id": 1, "source_document": "brd1.pdf",
         "action_total": 0, "action_mapped": 0, "trigger_total": 0, "rule_total": 0},
    ])
    assert docs[0]["mapping_status"] == "none"
    assert docs[0]["extraction_status"] == "pending"
    assert docs[0]["status"] == "empty"


def test_document_name_falls_back_to_workflow_name():
    docs = build_document_view([
        {"workflow_knowledge_id": 1, "workflow_name": "Loan BRD", "source_document": None,
         "action_total": 1, "action_mapped": 1},
    ])
    assert docs[0]["name"] == "Loan BRD"
