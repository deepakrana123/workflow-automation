"""
app/rbac/hierarchy.py

Workspace ancestor-chain resolution.

Pure function: get_ancestor_chain walks parent_id upward and returns the full
path from the global root down to the target workspace — in top-down order.

Example for a branch workspace:
  get_ancestor_chain(branch_ws_id, db)
  → [global_ws_id, region_ws_id, zone_ws_id, branch_ws_id]

Used by:
  - RuleInheritanceResolver  (collect rules from all ancestor levels)
  - PermissionChecker        (check if user holds permission anywhere in chain)
  - WorkflowPublicationService (traverse to find all effective rules)
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.workspace import Workspace


def get_ancestor_chain(workspace_id: int, db: Session) -> list[int]:
    """Return workspace IDs from global root down to workspace_id (inclusive).

    The list is ordered broadest-first:
      [global_id, region_id, zone_id, branch_id]

    If workspace_id does not exist or the chain is broken, returns whatever
    was resolved before the break. Never raises.

    Args:
        workspace_id: The leaf (target) workspace to start from.
        db: SQLAlchemy session.

    Returns:
        List of workspace IDs from root to target, inclusive.
        Returns [workspace_id] if no parent chain is found.
    """
    chain: list[int] = []
    seen: set[int] = set()          # cycle guard
    current_id: int | None = workspace_id

    while current_id is not None:
        if current_id in seen:
            break                   # cycle in data — stop
        seen.add(current_id)

        ws = db.query(Workspace).filter(Workspace.id == current_id).first()
        if ws is None:
            break

        chain.append(current_id)

        if ws.parent_id is None or ws.level == "global":
            break
        current_id = ws.parent_id

    # chain is currently leaf→root; reverse to root→leaf
    chain.reverse()
    return chain


def get_ancestor_chain_pure(workspace_id: int, workspaces: dict[int, dict]) -> list[int]:
    """Pure version — no DB. Accepts a pre-loaded dict of workspace dicts.

    Useful for unit tests and batch operations where DB round-trips are
    expensive.

    Args:
        workspace_id: The leaf workspace ID.
        workspaces: {id: {"id", "level", "parent_id"}} — ALL workspaces in the
                    system, keyed by ID. Subset is fine as long as the ancestor
                    chain is complete.

    Returns:
        List of workspace IDs from root to target, inclusive.
    """
    chain: list[int] = []
    seen: set[int] = set()
    current_id: int | None = workspace_id

    while current_id is not None:
        if current_id in seen:
            break
        seen.add(current_id)
        ws = workspaces.get(current_id)
        if ws is None:
            break
        chain.append(current_id)
        if ws.get("parent_id") is None or ws.get("level") == "global":
            break
        current_id = ws.get("parent_id")

    chain.reverse()
    return chain
