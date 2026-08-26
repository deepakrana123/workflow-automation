"""
Unit tests for RBACCapabilityResolver — pure logic, no DB.

Uses lightweight fakes instead of SQLAlchemy models so these run without
a database connection.
"""
from unittest.mock import MagicMock, patch
from app.runtime.context import RetrievalContext


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_action(id_, name, active=True):
    a = MagicMock()
    a.id = id_
    a.name = name
    a.active = active
    return a


def _make_workflow(steps):
    """steps: list of {"action": str, "id": str}"""
    wf = MagicMock()
    wf.parsed_rule_json = {"steps": steps}
    return wf


def _make_resolver(
    can_result=True,
    roles=None,
    all_action_ids=None,
    workflow=None,
):
    """Build a RBACCapabilityResolver with mocked DB and checker."""
    from app.runtime.rbac_resolver import RBACCapabilityResolver

    db = MagicMock()

    # Mock PermissionChecker
    checker = MagicMock()
    checker.can.return_value = can_result
    checker.get_roles.return_value = roles or []

    # Mock DB query for active action IDs
    if all_action_ids is not None:
        rows = [MagicMock(id=i) for i in all_action_ids]
        db.query.return_value.filter.return_value.all.return_value = rows

    resolver = RBACCapabilityResolver.__new__(RBACCapabilityResolver)
    resolver._db = db
    resolver._checker = checker

    # Patch internal helpers if needed
    if workflow is not None:
        resolver._get_workflow_action_ids = MagicMock(return_value=workflow)
    else:
        resolver._get_workflow_action_ids = MagicMock(return_value=None)

    resolver._get_step_action_ids = MagicMock(return_value=None)
    resolver._get_all_active_action_ids = MagicMock(
        return_value=set(all_action_ids or [])
    )

    return resolver


# ── Tests: global scope ───────────────────────────────────────────────────────

def test_no_capability_read_returns_empty_set():
    resolver = _make_resolver(can_result=False, all_action_ids={1, 2, 3})
    ctx = RetrievalContext(user_id="u1", workspace_id=1)
    result = resolver.resolve(ctx)
    assert result.allowed_action_ids == set()


def test_global_scope_returns_all_active_ids():
    resolver = _make_resolver(can_result=True, all_action_ids={10, 20, 30})
    ctx = RetrievalContext(user_id="u1", workspace_id=1)  # no workflow_id
    result = resolver.resolve(ctx)
    assert result.allowed_action_ids == {10, 20, 30}


def test_roles_are_populated():
    resolver = _make_resolver(
        can_result=True,
        roles=["branch_manager"],
        all_action_ids={1},
    )
    ctx = RetrievalContext(user_id="u1", workspace_id=1)
    result = resolver.resolve(ctx)
    assert "branch_manager" in result.roles


# ── Tests: workflow scope ─────────────────────────────────────────────────────

def test_workflow_scope_intersects_with_global():
    resolver = _make_resolver(
        can_result=True,
        all_action_ids={1, 2, 3, 4, 5},
        workflow={2, 4},               # only actions 2 and 4 in the workflow
    )
    ctx = RetrievalContext(user_id="u1", workspace_id=1, workflow_id=10)
    result = resolver.resolve(ctx)
    assert result.allowed_action_ids == {2, 4}


def test_workflow_scope_empty_when_workflow_has_no_actions():
    resolver = _make_resolver(
        can_result=True,
        all_action_ids={1, 2, 3},
        workflow=set(),
    )
    ctx = RetrievalContext(user_id="u1", workspace_id=1, workflow_id=10)
    result = resolver.resolve(ctx)
    assert result.allowed_action_ids == set()


def test_workflow_not_found_falls_back_to_global():
    resolver = _make_resolver(
        can_result=True,
        all_action_ids={1, 2, 3},
        workflow=None,   # None = workflow not found
    )
    ctx = RetrievalContext(user_id="u1", workspace_id=1, workflow_id=999)
    result = resolver.resolve(ctx)
    assert result.allowed_action_ids == {1, 2, 3}


# ── Tests: step scope ─────────────────────────────────────────────────────────

def test_step_scope_narrows_workflow_scope():
    resolver = _make_resolver(
        can_result=True,
        all_action_ids={1, 2, 3},
        workflow={1, 2},
    )
    resolver._get_step_action_ids = MagicMock(return_value={1})  # only action 1 at this step

    ctx = RetrievalContext(
        user_id="u1", workspace_id=1,
        workflow_id=10, current_step_id="step_2",
    )
    result = resolver.resolve(ctx)
    assert result.allowed_action_ids == {1}


def test_step_scope_empty_when_role_not_satisfied():
    resolver = _make_resolver(
        can_result=True,
        all_action_ids={1, 2, 3},
        workflow={1, 2},
    )
    resolver._get_step_action_ids = MagicMock(return_value=set())  # role mismatch → empty

    ctx = RetrievalContext(
        user_id="u1", workspace_id=1,
        workflow_id=10, current_step_id="step_2",
    )
    result = resolver.resolve(ctx)
    assert result.allowed_action_ids == set()


# ── Tests: can_execute_action ─────────────────────────────────────────────────

def test_can_execute_denied_when_no_permission():
    resolver = _make_resolver(can_result=False, all_action_ids={1})
    allowed, reason = resolver.can_execute_action("u1", 1, action_id=1)
    assert allowed is False
    assert reason == "CAPABILITY_READ_DENIED"


def test_can_execute_denied_when_action_not_in_workflow():
    resolver = _make_resolver(can_result=True, all_action_ids={1, 2})
    resolver._get_workflow_action_ids = MagicMock(return_value={2})  # action 1 not in workflow

    # Mock action lookup
    resolver._db.query.return_value.filter.return_value.first.return_value = MagicMock(id=1)

    allowed, reason = resolver.can_execute_action("u1", 1, action_id=1, workflow_id=10)
    assert allowed is False
    assert reason == "ACTION_NOT_IN_WORKFLOW"


def test_can_execute_allowed_when_all_checks_pass():
    resolver = _make_resolver(can_result=True, all_action_ids={1, 2})
    resolver._get_workflow_action_ids = MagicMock(return_value={1, 2})
    resolver._get_step_action_ids = MagicMock(return_value=None)

    action_mock = MagicMock(id=1)
    resolver._db.query.return_value.filter.return_value.first.return_value = action_mock

    allowed, reason = resolver.can_execute_action("u1", 1, action_id=1, workflow_id=10)
    assert allowed is True
    assert reason == "ALLOWED"
