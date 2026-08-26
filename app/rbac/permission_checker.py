"""
app/rbac/permission_checker.py

Deterministic RBAC permission resolution.

The LLM is never consulted here. The authoritative source is the
role_assignments table + the static ROLE_PERMISSIONS catalogue.

Ancestor-chain resolution:
  A user who holds region_manager in Region A automatically has that role's
  permissions for all zone and branch workspaces under Region A. This mirrors
  how a bank's org hierarchy works — a regional head can act on branch-level
  resources within their region.

Usage:
    checker = PermissionChecker(db)
    if not checker.can(user_id, "workflow:publish", workspace_id):
        raise HTTPException(403, ...)
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.role_assignment import RoleAssignment, get_permissions_for_role
from app.rbac.hierarchy import get_ancestor_chain
from app.core.logger import logger


class PermissionChecker:
    """RBAC permission resolver. Thread-safe — stateless beyond the DB session."""

    def __init__(self, db: Session):
        self._db = db

    def can(
        self,
        user_id: str | None,
        permission: str,
        workspace_id: int,
    ) -> bool:
        """Return True if user_id holds `permission` in workspace_id or any ancestor.

        Returns False (never raises) on any error — fail closed.

        Args:
            user_id:      The user's identity string. None → always False.
            permission:   A permission string, e.g. "workflow:publish".
            workspace_id: The workspace the operation targets.
        """
        if not user_id:
            return False

        try:
            # Collect the ancestor chain: [global, region, zone, branch=workspace_id]
            chain = get_ancestor_chain(workspace_id, self._db)
            if not chain:
                chain = [workspace_id]

            # Load all active role assignments for this user in the ancestor chain
            assignments = (
                self._db.query(RoleAssignment)
                .filter(
                    RoleAssignment.user_id == user_id,
                    RoleAssignment.workspace_id.in_(chain),
                    RoleAssignment.active.is_(True),
                )
                .all()
            )

            for assignment in assignments:
                perms = get_permissions_for_role(assignment.role)
                if permission in perms:
                    return True

            return False

        except Exception as exc:
            logger.warning(
                "permission_checker_error",
                extra={"extra_data": {
                    "user_id": user_id,
                    "permission": permission,
                    "workspace_id": workspace_id,
                    "error": str(exc),
                }},
            )
            return False

    def get_roles(self, user_id: str, workspace_id: int) -> list[str]:
        """Return all roles the user holds in workspace_id or any ancestor.

        Returns empty list on error.
        """
        if not user_id:
            return []
        try:
            chain = get_ancestor_chain(workspace_id, self._db)
            assignments = (
                self._db.query(RoleAssignment)
                .filter(
                    RoleAssignment.user_id == user_id,
                    RoleAssignment.workspace_id.in_(chain),
                    RoleAssignment.active.is_(True),
                )
                .all()
            )
            return [a.role for a in assignments]
        except Exception:
            return []

    def get_all_permissions(self, user_id: str, workspace_id: int) -> frozenset[str]:
        """Return the union of all permissions the user holds in the ancestor chain."""
        roles = self.get_roles(user_id, workspace_id)
        result: set[str] = set()
        for role in roles:
            result.update(get_permissions_for_role(role))
        return frozenset(result)


def can_pure(
    user_id: str | None,
    permission: str,
    workspace_id: int,
    assignments: list[dict],
    ancestor_chain: list[int],
) -> bool:
    """Pure version — no DB. For unit tests.

    Args:
        user_id:        The user identity.
        permission:     Permission to check.
        workspace_id:   Target workspace (not used directly — chain is passed in).
        assignments:    List of {user_id, role, workspace_id, active} dicts.
        ancestor_chain: Pre-resolved ancestor chain for workspace_id.
    """
    if not user_id:
        return False

    chain_set = set(ancestor_chain)
    for a in assignments:
        if (
            a.get("user_id") == user_id
            and a.get("workspace_id") in chain_set
            and a.get("active", True)
        ):
            perms = get_permissions_for_role(a.get("role", ""))
            if permission in perms:
                return True
    return False
