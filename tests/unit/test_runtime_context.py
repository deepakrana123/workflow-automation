"""Unit tests for runtime context dataclasses — pure, no DB."""

from app.runtime.context import (
    RetrievalContext,
    RuleEvaluationContext,
    RuleEvaluationResult,
)


# ── RetrievalContext ──────────────────────────────────────────────────────────

class TestRetrievalContext:
    def test_defaults(self):
        ctx = RetrievalContext(user_id="u1", workspace_id=1)
        assert ctx.workflow_id is None
        assert ctx.workflow_execution_id is None
        assert ctx.current_step_id is None
        assert ctx.allowed_action_ids is None
        assert ctx.roles == []
        assert ctx.metadata_filters == {}

    def test_has_workflow_scope_false_when_no_workflow(self):
        ctx = RetrievalContext(user_id="u1", workspace_id=1)
        assert ctx.has_workflow_scope() is False

    def test_has_workflow_scope_true_when_set(self):
        ctx = RetrievalContext(user_id="u1", workspace_id=1, workflow_id=42)
        assert ctx.has_workflow_scope() is True

    def test_has_step_scope_false_without_step(self):
        ctx = RetrievalContext(user_id="u1", workspace_id=1, workflow_id=1)
        assert ctx.has_step_scope() is False

    def test_has_step_scope_true_when_set(self):
        ctx = RetrievalContext(user_id="u1", workspace_id=1, workflow_id=1, current_step_id="s1")
        assert ctx.has_step_scope() is True

    def test_allowed_action_ids_none_means_unrestricted(self):
        ctx = RetrievalContext(user_id="u1", workspace_id=1)
        # None = not yet resolved, treated as "all allowed" in global scope
        assert ctx.allowed_action_ids is None

    def test_allowed_action_ids_empty_set_means_denied(self):
        ctx = RetrievalContext(user_id="u1", workspace_id=1)
        ctx.allowed_action_ids = set()
        assert ctx.allowed_action_ids == set()
        assert len(ctx.allowed_action_ids) == 0

    def test_roles_list_is_mutable(self):
        ctx = RetrievalContext(user_id="u1", workspace_id=1)
        ctx.roles = ["branch_manager"]
        assert "branch_manager" in ctx.roles


# ── RuleEvaluationContext ─────────────────────────────────────────────────────

class TestRuleEvaluationContext:
    def test_defaults(self):
        ctx = RuleEvaluationContext(user_id="u1", workspace_id=1)
        assert ctx.workflow_id is None
        assert ctx.actor_roles == []
        assert ctx.request_data == {}
        assert ctx.previous_step_outputs == {}

    def test_with_all_fields(self):
        ctx = RuleEvaluationContext(
            user_id="u1",
            workspace_id=5,
            workflow_id=10,
            workflow_execution_id=100,
            step_id="step_3",
            action_id=75,
            actor_roles=["branch_officer"],
            request_data={"loan_amount": 300000},
            previous_step_outputs={"credit_score": 720},
        )
        assert ctx.workflow_id == 10
        assert ctx.action_id == 75
        assert "branch_officer" in ctx.actor_roles
        assert ctx.request_data["loan_amount"] == 300000
        assert ctx.previous_step_outputs["credit_score"] == 720


# ── RuleEvaluationResult ──────────────────────────────────────────────────────

class TestRuleEvaluationResult:
    def test_allowed_result(self):
        r = RuleEvaluationResult(allowed=True)
        assert r.allowed is True
        assert r.failed_rules == []
        assert r.warnings == []
        d = r.to_dict()
        assert d["allowed"] is True
        assert d["failed_rules"] == []

    def test_denied_result_with_failures(self):
        r = RuleEvaluationResult(
            allowed=False,
            failed_rules=[{"rule_id": 1, "code": "LOAN_TOO_HIGH", "message": "Exceeds limit"}],
            warnings=["Near threshold"],
        )
        assert r.allowed is False
        assert len(r.failed_rules) == 1
        d = r.to_dict()
        assert d["allowed"] is False
        assert d["failed_rules"][0]["code"] == "LOAN_TOO_HIGH"
        assert d["warnings"] == ["Near threshold"]

    def test_to_dict_structure(self):
        r = RuleEvaluationResult(
            allowed=True,
            decisions=[{"result": True}],
        )
        d = r.to_dict()
        assert set(d.keys()) == {"allowed", "decisions", "failed_rules", "warnings"}
