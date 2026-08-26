"""Unit tests for SkillFileGenerator — deterministic, no DB required."""

from unittest.mock import MagicMock, patch, ANY
from app.workflow.skill_file_generator import SkillFileGenerator


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_workflow(steps, workspace_id=1, name="Test Workflow", domain="finance"):
    wf = MagicMock()
    wf.id              = 42
    wf.name            = name
    wf.domain          = domain
    wf.workspace_id    = workspace_id
    wf.skill_file_id   = None
    wf.skill_file_path = None
    wf.parsed_rule_json = {
        "trigger": {"event_type": "loan_application_received"},
        "steps": steps,
    }
    return wf


def _make_db(actors=None, action_rows=None, wk=None):
    db = MagicMock()

    # WorkflowKnowledge query
    wk_obj = MagicMock()
    wk_obj.id = 1
    db.query.return_value.filter.return_value.first.return_value = wk_obj

    # WorkflowActor query
    actor_result = MagicMock()
    actor_result.__iter__ = MagicMock(return_value=iter(actors or []))
    db.query.return_value.filter.return_value.all.return_value = actors or []

    return db


# ── Header section ────────────────────────────────────────────────────────────

def test_header_contains_workflow_name():
    gen  = SkillFileGenerator()
    wf   = _make_workflow([])

    with patch.object(gen, "_load_actions", return_value={}), \
         patch.object(gen, "_load_actors", return_value=[]), \
         patch("app.workflow.skill_file_generator.resolve_effective_rules", return_value=[]):
        content = gen.build(wf, MagicMock())

    assert "Test Workflow" in content
    assert "loan_application_received" in content
    assert "finance" in content


def test_header_contains_workflow_id():
    gen = SkillFileGenerator()
    wf  = _make_workflow([])
    with patch.object(gen, "_load_actions", return_value={}), \
         patch.object(gen, "_load_actors", return_value=[]), \
         patch("app.workflow.skill_file_generator.resolve_effective_rules", return_value=[]):
        content = gen.build(wf, MagicMock())
    assert "42" in content


# ── Step sections ─────────────────────────────────────────────────────────────

def test_each_step_gets_a_section():
    steps = [
        {"id": "s1", "action": "verify_kyc",    "depends_on": []},
        {"id": "s2", "action": "approve_loan",  "depends_on": ["s1"]},
    ]
    gen = SkillFileGenerator()
    wf  = _make_workflow(steps)

    with patch.object(gen, "_load_actions", return_value={
            "verify_kyc":   "Verify KYC",
            "approve_loan": "Approve Loan",
         }), \
         patch.object(gen, "_load_actors", return_value=[]), \
         patch("app.workflow.skill_file_generator.resolve_effective_rules", return_value=[]):
        content = gen.build(wf, MagicMock())

    assert "Step 1" in content
    assert "Step 2" in content
    assert "Verify KYC" in content
    assert "Approve Loan" in content


def test_step_with_routing_shows_branches():
    routing = {
        "field": "credit_score",
        "branches": [
            {"when": {"op": ">=", "value": 700}, "activate": ["s_approve"]},
            {"when": {"op": "<",  "value": 700}, "activate": ["s_reject"]},
        ],
        "default": ["s_manual"],
    }
    steps = [
        {"id": "s_check",   "action": "run_credit_check",  "depends_on": [], "routing": routing},
        {"id": "s_approve", "action": "approve_loan",      "depends_on": ["s_check"]},
        {"id": "s_reject",  "action": "reject_loan",       "depends_on": ["s_check"]},
        {"id": "s_manual",  "action": "manual_review",     "depends_on": ["s_check"]},
    ]
    gen = SkillFileGenerator()
    wf  = _make_workflow(steps)

    action_map = {
        "run_credit_check": "Run Credit Check",
        "approve_loan":     "Approve Loan",
        "reject_loan":      "Reject Loan",
        "manual_review":    "Manual Review",
    }
    with patch.object(gen, "_load_actions", return_value=action_map), \
         patch.object(gen, "_load_actors", return_value=[]), \
         patch("app.workflow.skill_file_generator.resolve_effective_rules", return_value=[]):
        content = gen.build(wf, MagicMock())

    assert "credit_score" in content
    assert ">=" in content
    assert "Routing decision" in content


# ── What can go wrong section ─────────────────────────────────────────────────

def test_risk_table_present():
    gen = SkillFileGenerator()
    wf  = _make_workflow([])
    with patch.object(gen, "_load_actions", return_value={}), \
         patch.object(gen, "_load_actors", return_value=[]), \
         patch("app.workflow.skill_file_generator.resolve_effective_rules", return_value=[]):
        content = gen.build(wf, MagicMock())
    assert "What can go wrong" in content


def test_rule_appears_in_risk_table():
    rule = MagicMock()
    rule.field         = "loan_amount"
    rule.op            = ">="
    rule.value         = 500000
    rule.description   = "Loan above 5L needs manager approval"
    rule.allowed_roles = ["branch_manager"]

    gen = SkillFileGenerator()
    wf  = _make_workflow([])

    with patch.object(gen, "_load_actions", return_value={}), \
         patch.object(gen, "_load_actors", return_value=[]), \
         patch("app.workflow.skill_file_generator.resolve_effective_rules", return_value=[rule]):
        content = gen.build(wf, MagicMock())

    assert "loan_amount" in content
    assert "RULE\\_BLOCKED" in content or "RULE_BLOCKED" in content


# ── Roles table ───────────────────────────────────────────────────────────────

def test_roles_table_section_present():
    gen = SkillFileGenerator()
    wf  = _make_workflow([])
    with patch.object(gen, "_load_actions", return_value={}), \
         patch.object(gen, "_load_actors", return_value=[]), \
         patch("app.workflow.skill_file_generator.resolve_effective_rules", return_value=[]):
        content = gen.build(wf, MagicMock())
    assert "Roles in this workflow" in content


def test_actor_appears_in_roles_table():
    actor      = MagicMock()
    actor.name = "Rama Devi"
    actor.role = "Branch Manager"

    gen = SkillFileGenerator()
    wf  = _make_workflow([])

    with patch.object(gen, "_load_actions", return_value={}), \
         patch.object(gen, "_load_actors", return_value=[actor]), \
         patch("app.workflow.skill_file_generator.resolve_effective_rules", return_value=[]):
        content = gen.build(wf, MagicMock())

    assert "Branch Manager" in content


# ── _step_roles helper ────────────────────────────────────────────────────────

def test_step_roles_from_embedded_rules():
    gen  = SkillFileGenerator()
    step = {
        "id": "s1", "action": "approve_loan",
        "business_rules": [
            {"field": "loan_amount", "op": ">=", "value": 500000,
             "allowed_roles": ["branch_manager", "zone_manager"]},
        ]
    }
    roles = gen._step_roles(step, eff_rules=[])
    assert "branch_manager" in roles
    assert "zone_manager" in roles


def test_step_roles_deduped():
    gen  = SkillFileGenerator()
    step = {
        "id": "s1", "action": "approve_loan",
        "business_rules": [
            {"allowed_roles": ["branch_manager"]},
            {"allowed_roles": ["branch_manager"]},
        ]
    }
    roles = gen._step_roles(step, eff_rules=[])
    assert roles.count("branch_manager") == 1
