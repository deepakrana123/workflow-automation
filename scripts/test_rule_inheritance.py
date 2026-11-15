"""
scripts/test_rule_inheritance.py

Tests for the flat-architecture resolve_effective_rules().

Run from project root:
    .venv312\\Scripts\\python.exe scripts/test_rule_inheritance.py
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv; load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
import app.models

failures: list[str] = []


# ── Helpers ───────────────────────────────────────────────────────────────────

def _session():
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy import JSON
    for t in Base.metadata.tables.values():
        for c in t.columns:
            if isinstance(c.type, JSONB):
                c.type = JSON()
    e = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(e)
    return sessionmaker(bind=e)()


def _seed(db, tenant_id=1, workspace_id=1):
    from app.models.tenant import Tenant
    from app.models.workspace import Workspace
    db.add_all([
        Tenant(id=tenant_id, name=f"b{tenant_id}",
               slug=f"b-{tenant_id}", display_name=f"B{tenant_id}", active=True),
        Workspace(id=workspace_id, tenant_id=tenant_id,
                  name="personal_loan", display_name="Personal Loan", active=True),
    ])
    db.commit()


def _make_rule(db, workspace_id, description, field=None, op=None, value=None,
               active=True, locked=False, allowed_roles=None):
    from app.models.business_rule_definition import BusinessRuleDefinition
    r = BusinessRuleDefinition(
        scope_workspace_id=workspace_id,
        description=description,
        field=field,
        op=op,
        value=value,
        allowed_roles=allowed_roles or [],
        locked=locked,
        active=active,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def chk(name: str, cond: bool, detail: str = "") -> None:
    icon = "✓" if cond else "✗"
    print(f"  {icon}  {name}" + (f"  — {detail}" if detail else ""))
    if not cond:
        failures.append(name)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_rules_from_workspace_returned():
    print("\n[1] Active rules from the requested workspace are returned")
    from app.rbac.rule_inheritance import resolve_effective_rules
    db = _session(); _seed(db, workspace_id=1)
    _make_rule(db, 1, "CIBIL >= 700", field="credit_score", op=">=", value=700)
    _make_rule(db, 1, "Loan amount <= 50 lakh", field="loan_amount", op="<=", value=5000000)
    rules = resolve_effective_rules(1, db)
    chk("2 rules returned", len(rules) == 2, str(len(rules)))
    descs = {r.description for r in rules}
    chk("CIBIL rule present", "CIBIL >= 700" in descs)
    chk("Loan amount rule present", "Loan amount <= 50 lakh" in descs)
    db.close()


def test_rules_from_other_workspace_excluded():
    print("\n[2] Rules from another workspace are never returned")
    from app.rbac.rule_inheritance import resolve_effective_rules
    from app.models.tenant import Tenant
    from app.models.workspace import Workspace
    db = _session()
    _seed(db, tenant_id=1, workspace_id=1)
    # Second workspace — different tenant so no composite constraint conflict
    db.add_all([
        Tenant(id=2, name="b2", slug="b-2", display_name="B2", active=True),
        Workspace(id=2, tenant_id=2, name="personal_loan",
                  display_name="Personal Loan", active=True),
    ])
    db.commit()
    _make_rule(db, 1, "WS1 rule", field="credit_score", op=">=", value=700)
    _make_rule(db, 2, "WS2 rule", field="loan_amount",  op="<=", value=1000000)

    ws1_rules = resolve_effective_rules(1, db)
    ws2_rules = resolve_effective_rules(2, db)

    chk("WS1 returns only its own rule", len(ws1_rules) == 1)
    chk("WS1 rule is correct", ws1_rules[0].description == "WS1 rule")
    chk("WS2 returns only its own rule", len(ws2_rules) == 1)
    chk("WS2 rule is correct", ws2_rules[0].description == "WS2 rule")
    chk("WS1 rules have no WS2 data",
        all(r.scope_workspace_id == 1 for r in ws1_rules))
    chk("WS2 rules have no WS1 data",
        all(r.scope_workspace_id == 2 for r in ws2_rules))
    db.close()


def test_inactive_rules_excluded():
    print("\n[3] Inactive rules (active=False) are excluded")
    from app.rbac.rule_inheritance import resolve_effective_rules
    db = _session(); _seed(db)
    _make_rule(db, 1, "Active rule",   active=True)
    _make_rule(db, 1, "Inactive rule", active=False)
    rules = resolve_effective_rules(1, db)
    chk("only 1 rule returned", len(rules) == 1, str(len(rules)))
    chk("active rule returned", rules[0].description == "Active rule")
    chk("inactive rule excluded",
        all(r.description != "Inactive rule" for r in rules))
    db.close()


def test_field_filter_respected():
    print("\n[4] Optional field filter returns only matching rules")
    from app.rbac.rule_inheritance import resolve_effective_rules
    db = _session(); _seed(db)
    _make_rule(db, 1, "CIBIL rule",  field="credit_score", op=">=", value=700)
    _make_rule(db, 1, "Income rule", field="annual_income", op=">=", value=300000)
    _make_rule(db, 1, "Text rule",   field=None)

    cibil_rules  = resolve_effective_rules(1, db, field="credit_score")
    income_rules = resolve_effective_rules(1, db, field="annual_income")
    all_rules    = resolve_effective_rules(1, db)

    chk("credit_score filter: 1 rule", len(cibil_rules) == 1)
    chk("credit_score rule correct",   cibil_rules[0].description == "CIBIL rule")
    chk("annual_income filter: 1 rule", len(income_rules) == 1)
    chk("annual_income rule correct",   income_rules[0].description == "Income rule")
    chk("no filter: 3 rules",          len(all_rules) == 3, str(len(all_rules)))
    db.close()


def test_locked_rules_included():
    print("\n[5] Locked rules are included (locked is a metadata flag, not an exclusion)")
    from app.rbac.rule_inheritance import resolve_effective_rules
    db = _session(); _seed(db)
    _make_rule(db, 1, "Unlocked rule", locked=False)
    _make_rule(db, 1, "Locked rule",   locked=True)
    rules = resolve_effective_rules(1, db)
    chk("both rules returned", len(rules) == 2, str(len(rules)))
    locked = [r for r in rules if r.locked]
    chk("locked rule present", len(locked) == 1)
    chk("locked rule correct", locked[0].description == "Locked rule")
    db.close()


def test_allowed_roles_preserved():
    print("\n[6] allowed_roles field is preserved on returned rules")
    from app.rbac.rule_inheritance import resolve_effective_rules
    db = _session(); _seed(db)
    _make_rule(db, 1, "BM rule",
               field="loan_amount", op=">=", value=500000,
               allowed_roles=["branch_manager"])
    rules = resolve_effective_rules(1, db)
    chk("1 rule returned", len(rules) == 1)
    chk("allowed_roles correct",
        rules[0].allowed_roles == ["branch_manager"])
    db.close()


def test_no_rules_for_workspace_returns_empty():
    print("\n[7] Workspace with no rules returns empty list")
    from app.rbac.rule_inheritance import resolve_effective_rules
    db = _session(); _seed(db)
    rules = resolve_effective_rules(1, db)
    chk("empty list returned", rules == [])
    db.close()


def test_nonexistent_workspace_returns_empty():
    print("\n[8] Non-existent workspace_id returns empty list (no crash)")
    from app.rbac.rule_inheritance import resolve_effective_rules
    db = _session(); _seed(db)
    rules = resolve_effective_rules(99999, db)
    chk("empty list for unknown workspace", rules == [])
    db.close()


def test_no_access_to_parent_id_or_level():
    print("\n[9] resolve_effective_rules does not access parent_id or level")
    import ast, pathlib
    src = pathlib.Path("app/rbac/rule_inheritance.py").read_text()
    tree = ast.parse(src)
    # Collect all Attribute and Name nodes that reference hierarchy fields
    forbidden = {"parent_id", "level", "get_ancestor_chain",
                 "get_ancestor_chain_pure", "hierarchy"}
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in forbidden:
            found.add(node.attr)
        if isinstance(node, ast.Name) and node.id in forbidden:
            found.add(node.id)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for f in forbidden:
                if f in node.value:
                    found.add(f)
    chk("no hierarchy references in rule_inheritance.py", not found,
        f"found: {found}" if found else "")
    db = _session(); _seed(db)
    db.close()


def test_validate_new_rule_always_empty():
    print("\n[10] validate_new_rule returns [] — no inherited constraints in flat arch")
    from app.rbac.rule_inheritance import validate_new_rule
    db = _session(); _seed(db)
    _make_rule(db, 1, "CIBIL >= 700", field="credit_score", op=">=", value=700)
    # Even a 'loosening' rule should return no violations in flat arch
    violations = validate_new_rule(
        new_rule={"field": "credit_score", "op": ">=",
                  "value": 500, "description": "looser rule"},
        workspace_id=1,
        db=db,
    )
    chk("no violations returned", violations == [], str(violations))
    # Verify the function signature remains intact
    import inspect
    from app.rbac.rule_inheritance import validate_new_rule as vnr
    sig = inspect.signature(vnr)
    params = list(sig.parameters)
    chk("signature has new_rule, workspace_id, db",
        params == ["new_rule", "workspace_id", "db"])
    db.close()


def test_is_more_restrictive_pure_function_unchanged():
    print("\n[11] is_more_restrictive() pure function still works correctly")
    from app.rbac.rule_inheritance import is_more_restrictive
    # >= : higher value is more restrictive
    chk("700 >= 500 is more restrictive",
        is_more_restrictive({"field": "credit_score", "op": ">=", "value": 700},
                            {"field": "credit_score", "op": ">=", "value": 500}))
    chk("400 >= 500 is NOT more restrictive",
        not is_more_restrictive({"field": "credit_score", "op": ">=", "value": 400},
                                {"field": "credit_score", "op": ">=", "value": 500}))
    # <= : lower value is more restrictive
    chk("40 <= 50 is more restrictive",
        is_more_restrictive({"field": "foir", "op": "<=", "value": 40},
                            {"field": "foir", "op": "<=", "value": 50}))
    chk("60 <= 50 is NOT more restrictive",
        not is_more_restrictive({"field": "foir", "op": "<=", "value": 60},
                                {"field": "foir", "op": "<=", "value": 50}))
    # Different fields — always compatible
    chk("different fields always compatible",
        is_more_restrictive({"field": "credit_score", "op": ">=", "value": 400},
                            {"field": "loan_amount",  "op": ">=", "value": 500}))


def test_resolve_effective_rules_signature_unchanged():
    print("\n[12] resolve_effective_rules() signature preserved for all callers")
    import inspect
    from app.rbac.rule_inheritance import resolve_effective_rules
    sig = inspect.signature(resolve_effective_rules)
    params = list(sig.parameters)
    chk("params are workspace_id, db, field",
        params == ["workspace_id", "db", "field"])
    # field must default to None
    chk("field defaults to None",
        sig.parameters["field"].default is None)


# ── Runner ────────────────────────────────────────────────────────────────────

def main() -> int:
    print("=" * 60)
    print("rule_inheritance.py — Flat Architecture Tests")
    print("=" * 60)
    for t in [
        test_rules_from_workspace_returned,
        test_rules_from_other_workspace_excluded,
        test_inactive_rules_excluded,
        test_field_filter_respected,
        test_locked_rules_included,
        test_allowed_roles_preserved,
        test_no_rules_for_workspace_returns_empty,
        test_nonexistent_workspace_returns_empty,
        test_no_access_to_parent_id_or_level,
        test_validate_new_rule_always_empty,
        test_is_more_restrictive_pure_function_unchanged,
        test_resolve_effective_rules_signature_unchanged,
    ]:
        try:
            t()
        except Exception as exc:
            print(f"  [UNEXPECTED] {exc}")
            traceback.print_exc()
            failures.append(t.__name__)
    print("\n" + "=" * 60)
    if failures:
        print(f"FAILED — {len(failures)}: " + ", ".join(failures))
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
