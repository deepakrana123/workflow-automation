"""Unit tests for WorkflowPublicationService gate checks."""

from unittest.mock import MagicMock, patch

from app.workflow.publication_service import WorkflowPublicationService


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_workflow(workspace_id=1, status="active", steps=None):
    wf = MagicMock()
    wf.id              = 10
    wf.status          = status
    wf.workspace_id    = workspace_id
    wf.parsed_rule_json = {"steps": steps or []}
    return wf


def _svc():
    return WorkflowPublicationService()


# ── workflow_not_found ────────────────────────────────────────────────────────

def test_returns_error_when_workflow_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    result = _svc().publish(99, user_id="alice", db=db)
    assert result.success is False
    assert result.error == "workflow_not_found"


def test_returns_error_when_already_published():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = _make_workflow(status="published")
    result = _svc().publish(10, user_id="alice", db=db)
    assert result.success is False
    assert result.error == "already_published"


# ── Gate 1: RBAC ─────────────────────────────────────────────────────────────

def test_gate1_fails_when_no_user_id():
    db  = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = _make_workflow()
    svc = _svc()

    with patch("app.workflow.publication_service.PermissionChecker") as MockChecker:
        MockChecker.return_value.can.return_value = False
        result = svc.publish(10, user_id=None, db=db)

    # Gate 1 RBAC check — should fail with no user
    gate1 = next((c for c in result.checks if c.check == "rbac"), None)
    assert gate1 is not None
    assert gate1.passed is False


def test_gate1_passes_with_permission():
    db  = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = _make_workflow()
    svc = _svc()

    with patch("app.workflow.publication_service.PermissionChecker") as MockChecker, \
         patch("app.workflow.publication_service.resolve_effective_rules", return_value=[]), \
         patch("app.workflow.publication_service.detect_rule_conflicts", return_value=[]), \
         patch("app.workflow.publication_service.audit_create"), \
         patch("app.workflow.skill_file_generator.SkillFileGenerator.generate"):
        MockChecker.return_value.can.return_value = True
        result = svc.publish(10, user_id="alice", db=db)

    gate1 = next((c for c in result.checks if c.check == "rbac"), None)
    assert gate1 is not None
    assert gate1.passed is True


# ── Gate 2: HumanTask role coverage ──────────────────────────────────────────

def test_gate2_passes_with_no_human_task_steps():
    """No human_task steps → gate always passes."""
    steps = [
        {"id": "s1", "action": "verify_kyc", "depends_on": []},
    ]
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = _make_workflow(steps=steps)
    svc = _svc()

    with patch("app.workflow.publication_service.PermissionChecker") as MockChecker, \
         patch("app.workflow.publication_service.resolve_effective_rules", return_value=[]), \
         patch("app.workflow.publication_service.detect_rule_conflicts", return_value=[]), \
         patch("app.workflow.publication_service.audit_create"), \
         patch("app.workflow.skill_file_generator.SkillFileGenerator.generate"):
        MockChecker.return_value.can.return_value = True
        result = svc.publish(10, user_id="alice", db=db)

    ht_checks = [c for c in result.checks if c.check == "human_task_roles"]
    assert all(c.passed for c in ht_checks)


def test_gate2_fails_when_human_task_step_has_no_roles():
    steps = [
        {
            "id": "s1", "action": "approve_loan",
            "execution_type": "human_task",
            "business_rules": [],   # empty allowed_roles
        }
    ]
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = _make_workflow(steps=steps)
    svc = _svc()

    with patch("app.workflow.publication_service.PermissionChecker") as MockChecker, \
         patch("app.workflow.publication_service.resolve_effective_rules", return_value=[]), \
         patch("app.workflow.publication_service.detect_rule_conflicts", return_value=[]):
        MockChecker.return_value.can.return_value = True
        result = svc.publish(10, user_id="alice", db=db)

    ht_checks = [c for c in result.checks if c.check == "human_task_roles"]
    assert any(not c.passed for c in ht_checks)
    assert result.success is False


# ── Gate 3: Rule conflicts ────────────────────────────────────────────────────

def test_gate3_fails_when_conflicts_exist():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = _make_workflow()
    svc = _svc()

    conflict = {"type": "threshold_conflict", "subject": "approval required above",
                "rules": [{"rule": "r1"}, {"rule": "r2"}]}

    with patch("app.workflow.publication_service.PermissionChecker") as MockChecker, \
         patch("app.workflow.publication_service.resolve_effective_rules", return_value=[]), \
         patch("app.workflow.publication_service.detect_rule_conflicts", return_value=[conflict]):
        MockChecker.return_value.can.return_value = True
        result = svc.publish(10, user_id="alice", db=db)

    gate3 = next((c for c in result.checks if c.check == "rule_conflicts"), None)
    assert gate3 is not None
    assert gate3.passed is False
    assert result.success is False


def test_gate3_passes_with_no_conflicts():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = _make_workflow()
    svc = _svc()

    with patch("app.workflow.publication_service.PermissionChecker") as MockChecker, \
         patch("app.workflow.publication_service.resolve_effective_rules", return_value=[]), \
         patch("app.workflow.publication_service.detect_rule_conflicts", return_value=[]), \
         patch("app.workflow.publication_service.audit_create"), \
         patch("app.workflow.skill_file_generator.SkillFileGenerator.generate"):
        MockChecker.return_value.can.return_value = True
        result = svc.publish(10, user_id="alice", db=db)

    gate3 = next((c for c in result.checks if c.check == "rule_conflicts"), None)
    assert gate3 is not None
    assert gate3.passed is True


# ── All gates pass ────────────────────────────────────────────────────────────

def test_all_gates_pass_publishes():
    db = MagicMock()
    wf = _make_workflow()
    db.query.return_value.filter.return_value.first.return_value = wf
    svc = _svc()

    with patch("app.workflow.publication_service.PermissionChecker") as MockChecker, \
         patch("app.workflow.publication_service.resolve_effective_rules", return_value=[]), \
         patch("app.workflow.publication_service.detect_rule_conflicts", return_value=[]), \
         patch("app.workflow.publication_service.audit_create"), \
         patch("app.workflow.skill_file_generator.SkillFileGenerator.generate"):
        MockChecker.return_value.can.return_value = True
        result = svc.publish(10, user_id="alice", db=db)

    assert result.success is True
    assert wf.status == "published"
