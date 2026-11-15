"""
app/rbac/rule_inheritance.py

Effective rule resolution for a flat workspace architecture.

Architecture note
-----------------
Workspaces are flat (Tenant → Workspace, no parent-child hierarchy).
Each BusinessRuleDefinition is scoped to exactly one workspace via
`scope_workspace_id`.  Rule inheritance across workspaces does not exist
in this architecture.

`resolve_effective_rules()` therefore returns all active
BusinessRuleDefinition rows whose `scope_workspace_id` matches the
requested workspace — no ancestor chain, no cross-workspace lookup.

`validate_new_rule()` is preserved for call-site compatibility.  With a
flat architecture there are no ancestor constraints to validate against,
so it always returns an empty violations list.

`is_more_restrictive()` is preserved unchanged — it is a pure function
used by callers that may compare rules independently of the hierarchy.

Callers that depended on inherited ordering (global → branch) previously
received rules in root-first order.  With a flat architecture the concept
of ordering by level does not apply; rules are returned in ascending `id`
order (insertion order), which is deterministic and stable.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.business_rule_definition import BusinessRuleDefinition


def resolve_effective_rules(
    workspace_id: int,
    db: Session,
    field: str | None = None,
) -> list[BusinessRuleDefinition]:
    """Return all active BusinessRuleDefinition rows for a workspace.

    With the flat workspace architecture (no parent-child hierarchy) the
    effective rule set is exactly the set of rules declared on the
    workspace itself.  No ancestor chain is walked.

    Args:
        workspace_id: The workspace whose rules are requested.
        db:           SQLAlchemy session.
        field:        Optional field name to filter by.  Pass None to
                      return all rules for the workspace.

    Returns:
        List of active BusinessRuleDefinition rows scoped to workspace_id,
        ordered by id ascending.  Returns an empty list if the workspace
        has no active rules or does not exist.
    """
    q = (
        db.query(BusinessRuleDefinition)
        .filter(
            BusinessRuleDefinition.scope_workspace_id == workspace_id,
            BusinessRuleDefinition.active.is_(True),
        )
    )
    if field:
        q = q.filter(BusinessRuleDefinition.field == field)

    return q.order_by(BusinessRuleDefinition.id.asc()).all()


def is_more_restrictive(
    new_rule: dict,
    inherited_rule: dict,
) -> bool:
    """Pure function. Return True if new_rule is at least as restrictive as inherited_rule.

    Both arguments are dicts with keys: field, op, value.

    Returns True (allowed) when:
      - Different fields or ops — rules don't conflict
      - new rule tightens the boundary the inherited rule set

    Returns False (rejected) when the new rule would LOOSEN the boundary.

    Args:
        new_rule:       {"field": str, "op": str, "value": any}
        inherited_rule: {"field": str, "op": str, "value": any}
    """
    if new_rule.get("field") != inherited_rule.get("field"):
        return True   # Different fields — not in conflict

    new_op  = new_rule.get("op")
    inh_op  = inherited_rule.get("op")
    new_val = new_rule.get("value")
    inh_val = inherited_rule.get("value")

    if new_op != inh_op:
        return True   # Different operators — let the rule engine sort it out

    try:
        if new_op in (">=", ">"):
            return float(new_val) >= float(inh_val)

        if new_op in ("<=", "<"):
            return float(new_val) <= float(inh_val)

        if new_op == "==":
            return new_val == inh_val

        if new_op == "in":
            try:
                return set(new_val) <= set(inh_val)
            except TypeError:
                return False

        if new_op == "not_in":
            try:
                return set(new_val) >= set(inh_val)
            except TypeError:
                return False

    except (TypeError, ValueError):
        return False

    return True   # Unknown op — don't block


def validate_new_rule(
    new_rule: dict,
    workspace_id: int,
    db: Session,
) -> list[str]:
    """Check whether a new rule would loosen any inherited constraint.

    With the flat workspace architecture there is no inheritance hierarchy,
    so there are no ancestor constraints to validate against.  This function
    is preserved for call-site compatibility and always returns an empty list.

    Args:
        new_rule:     {"field": str, "op": str, "value": any, "description": str}
        workspace_id: The workspace where the rule would be declared.
        db:           SQLAlchemy session (unused; retained for signature compat).

    Returns:
        Always [].  No violations are possible without a hierarchy.
    """
    return []
