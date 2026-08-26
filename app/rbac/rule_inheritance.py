"""
app/rbac/rule_inheritance.py

RuleInheritanceResolver — collects the effective rule set for a workspace
by walking the ancestor chain and gathering all active BusinessRuleDefinition
rows declared at any ancestor level.

Rule ordering: global rules come first, branch rules last.
  [global_rules, region_rules, zone_rules, branch_rules]

This ordering matters for restriction enforcement: when a step is evaluated,
global rules apply first. A branch rule can only ADD more restriction, not
reduce a global rule's threshold.

Restriction enforcement (write-time check):
  is_more_restrictive(new_rule, inherited_rule) → bool

  For >= (lower bound): new_value >= inherited_value  (higher = more restrictive)
  For <= (upper bound): new_value <= inherited_value  (lower = more restrictive)
  For ==: must match exactly
  For in: new_set must be a subset of inherited_set

If a new rule fails the restriction check against ANY inherited rule for the
same field+op combination, it is rejected.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.business_rule_definition import BusinessRuleDefinition
from app.rbac.hierarchy import get_ancestor_chain


def resolve_effective_rules(
    workspace_id: int,
    db: Session,
    field: str | None = None,
) -> list[BusinessRuleDefinition]:
    """Return the ordered effective rule set for a workspace.

    Collects all active BusinessRuleDefinition rows whose scope_workspace_id
    is in the ancestor chain of workspace_id (inclusive of workspace_id).
    Ordered from global to branch.

    Args:
        workspace_id: The target workspace.
        db: SQLAlchemy session.
        field: If provided, filter to rules for this specific field only.
               Pass None to get all rules.

    Returns:
        List of BusinessRuleDefinition ordered from root to leaf.
    """
    chain = get_ancestor_chain(workspace_id, db)
    if not chain:
        chain = [workspace_id]

    q = (
        db.query(BusinessRuleDefinition)
        .filter(
            BusinessRuleDefinition.scope_workspace_id.in_(chain),
            BusinessRuleDefinition.active.is_(True),
        )
    )
    if field:
        q = q.filter(BusinessRuleDefinition.field == field)

    all_rules = q.all()

    # Sort by chain position so global rules come first
    chain_index = {ws_id: idx for idx, ws_id in enumerate(chain)}
    all_rules.sort(key=lambda r: chain_index.get(r.scope_workspace_id, 999))

    return all_rules


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

    new_op   = new_rule.get("op")
    inh_op   = inherited_rule.get("op")
    new_val  = new_rule.get("value")
    inh_val  = inherited_rule.get("value")

    if new_op != inh_op:
        return True   # Different operators — let the rule engine sort it out

    try:
        if new_op in (">=", ">"):
            # Lower bound — more restrictive means HIGHER threshold
            return float(new_val) >= float(inh_val)

        if new_op in ("<=", "<"):
            # Upper bound — more restrictive means LOWER threshold
            return float(new_val) <= float(inh_val)

        if new_op == "==":
            # Must be identical
            return new_val == inh_val

        if new_op == "in":
            # More restrictive means a SMALLER allowed set
            try:
                return set(new_val) <= set(inh_val)
            except TypeError:
                return False

        if new_op == "not_in":
            # More restrictive means a LARGER excluded set
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

    Returns a list of violation messages. Empty list = rule is valid.

    Args:
        new_rule:     {"field": str, "op": str, "value": any, "description": str}
        workspace_id: The workspace where the rule would be declared.
        db:           SQLAlchemy session.
    """
    field = new_rule.get("field")
    if not field:
        return []   # Description-only rule — nothing to validate

    # Only check inherited rules, not the workspace's own rules
    chain = get_ancestor_chain(workspace_id, db)
    ancestor_ids = [ws_id for ws_id in chain if ws_id != workspace_id]

    if not ancestor_ids:
        return []   # global workspace — no inheritance

    inherited = (
        db.query(BusinessRuleDefinition)
        .filter(
            BusinessRuleDefinition.scope_workspace_id.in_(ancestor_ids),
            BusinessRuleDefinition.field == field,
            BusinessRuleDefinition.active.is_(True),
        )
        .all()
    )

    violations = []
    for inh in inherited:
        inh_dict = {"field": inh.field, "op": inh.op, "value": inh.value}
        if not is_more_restrictive(new_rule, inh_dict):
            violations.append(
                f"Rule '{new_rule.get('description', '')}' "
                f"relaxes an inherited constraint from workspace {inh.scope_workspace_id}: "
                f"{inh.description}"
            )
    return violations
