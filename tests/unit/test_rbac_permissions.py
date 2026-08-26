"""Unit tests for RBAC permission checking (pure version — no DB)."""

from app.rbac.permission_checker import can_pure
from app.models.role_assignment import (
    VALID_ROLES,
    ROLE_PERMISSIONS,
    get_permissions_for_role,
)


# ── Role catalogue ────────────────────────────────────────────────────────────

def test_all_roles_defined():
    assert "global_admin" in VALID_ROLES
    assert "branch_officer" in VALID_ROLES
    assert "read_only" in VALID_ROLES


def test_global_admin_has_all_key_permissions():
    perms = get_permissions_for_role("global_admin")
    for p in ("workflow:publish", "rule:override", "admin:manage_roles", "audit:read"):
        assert p in perms, f"global_admin missing {p}"


def test_read_only_has_only_read_permissions():
    perms = get_permissions_for_role("read_only")
    assert "workflow:read" in perms
    assert "workflow:publish" not in perms
    assert "rule:create" not in perms
    assert "admin:manage_roles" not in perms


def test_auditor_has_audit_read_not_write():
    perms = get_permissions_for_role("auditor")
    assert "audit:read" in perms
    assert "workflow:publish" not in perms
    assert "rule:create" not in perms


def test_branch_officer_cannot_publish():
    perms = get_permissions_for_role("branch_officer")
    assert "workflow:publish" not in perms
    assert "humantask:resolve" in perms


def test_unknown_role_returns_empty():
    assert get_permissions_for_role("super_overlord") == frozenset()


# ── can_pure ─────────────────────────────────────────────────────────────────

def _assignment(user_id, role, workspace_id, active=True):
    return {"user_id": user_id, "role": role, "workspace_id": workspace_id, "active": active}


CHAIN = [1, 2, 3, 4]   # global=1, region=2, zone=3, branch=4


def test_user_with_correct_role_is_allowed():
    assignments = [_assignment("alice", "branch_manager", 4)]
    assert can_pure("alice", "workflow:publish", 4, assignments, CHAIN) is True


def test_user_with_ancestor_role_allowed_in_child():
    # region_manager assigned at workspace 2 can publish in workspace 4
    assignments = [_assignment("bob", "region_manager", 2)]
    assert can_pure("bob", "workflow:publish", 4, assignments, CHAIN) is True


def test_user_without_any_assignment_denied():
    assert can_pure("charlie", "workflow:publish", 4, [], CHAIN) is False


def test_read_only_cannot_publish():
    assignments = [_assignment("diana", "read_only", 4)]
    assert can_pure("diana", "workflow:publish", 4, assignments, CHAIN) is False


def test_inactive_assignment_denied():
    assignments = [_assignment("eve", "branch_manager", 4, active=False)]
    assert can_pure("eve", "workflow:publish", 4, assignments, CHAIN) is False


def test_none_user_id_always_denied():
    assignments = [_assignment("alice", "global_admin", 1)]
    assert can_pure(None, "workflow:publish", 4, assignments, CHAIN) is False


def test_assignment_outside_chain_not_counted():
    # workspace 99 is not in chain [1,2,3,4]
    assignments = [_assignment("frank", "global_admin", 99)]
    assert can_pure("frank", "workflow:publish", 4, assignments, CHAIN) is False


def test_auditor_can_read_audit_logs():
    assignments = [_assignment("grace", "auditor", 2)]
    assert can_pure("grace", "audit:read", 4, assignments, CHAIN) is True


def test_branch_officer_can_resolve_human_task():
    assignments = [_assignment("henry", "branch_officer", 4)]
    assert can_pure("henry", "humantask:resolve", 4, assignments, CHAIN) is True
