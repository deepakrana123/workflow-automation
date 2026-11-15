"""
scripts/test_rule_extraction.py

Tests for RuleExtractionService.extract_for_knowledge().

Run from project root:
    .venv312\\Scripts\\python.exe scripts/test_rule_extraction.py
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
        Tenant(id=tenant_id, name=f"b{tenant_id}", slug=f"b-{tenant_id}",
               display_name=f"Bank {tenant_id}", active=True),
        Workspace(id=workspace_id, tenant_id=tenant_id,
                  name="personal_loan", display_name="Personal Loan", active=True),
    ])
    db.commit()


def _make_knowledge(db, workspace_id=1, brd_document_id=None,
                    workflow_name="PL Workflow"):
    from app.models.workflow_knowledge import WorkflowKnowledge
    wk = WorkflowKnowledge(
        workflow_name=workflow_name,
        summary="Test BRD",
        workspace_id=workspace_id,
        source_document="test.pdf",
        brd_document_id=brd_document_id,
    )
    db.add(wk)
    db.flush()
    return wk


def _make_raw_rule(db, knowledge_id, rule_text,
                   condition=None, outcome=None,
                   responsible_role=None, threshold=None,
                   brd_document_id=None):
    from app.models.workflow_business_rule import WorkflowBusinessRule
    r = WorkflowBusinessRule(
        workflow_knowledge_id=knowledge_id,
        rule=rule_text,
        condition=condition,
        outcome=outcome,
        responsible_role=responsible_role,
        threshold=threshold,
        source_brd_document_id=brd_document_id,
    )
    db.add(r)
    db.flush()
    return r


def chk(name: str, cond: bool, detail: str = "") -> None:
    icon = "✓" if cond else "✗"
    print(f"  {icon}  {name}" + (f"  — {detail}" if detail else ""))
    if not cond:
        failures.append(name)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_only_rules_for_requested_knowledge_processed():
    print("\n[1] Only rules belonging to the requested WorkflowKnowledge are processed")
    from app.rbac.rule_extractor import RuleExtractionService
    from app.models.business_rule_definition import BusinessRuleDefinition
    db = _session(); _seed(db)
    wk_a = _make_knowledge(db, workspace_id=1)
    wk_b = _make_knowledge(db, workspace_id=1, workflow_name="Other BRD")
    _make_raw_rule(db, wk_a.id, "CIBIL >= 700")
    _make_raw_rule(db, wk_a.id, "Loan amount <= 50 lakh")
    _make_raw_rule(db, wk_b.id, "Min income >= 25000")
    db.commit()

    svc = RuleExtractionService()
    result = svc.extract_for_knowledge(db, wk_a.id)

    chk("rules_created = 2 (only wk_a)", result["rules_created"] == 2,
        str(result["rules_created"]))
    chk("rules_skipped = 0", result["rules_skipped"] == 0)

    # Confirm only wk_a's rules have definitions
    defs_a = db.query(BusinessRuleDefinition).filter(
        BusinessRuleDefinition.source_workflow_knowledge_id == wk_a.id
    ).all()
    defs_b = db.query(BusinessRuleDefinition).filter(
        BusinessRuleDefinition.source_workflow_knowledge_id == wk_b.id
    ).all()
    chk("2 definitions for wk_a", len(defs_a) == 2)
    chk("0 definitions for wk_b (not processed)", len(defs_b) == 0)
    db.close()


def test_definitions_link_exact_raw_rule():
    print("\n[2] Definitions link to the exact raw WorkflowBusinessRule")
    from app.rbac.rule_extractor import RuleExtractionService
    from app.models.business_rule_definition import BusinessRuleDefinition
    db = _session(); _seed(db)
    wk = _make_knowledge(db, workspace_id=1)
    raw1 = _make_raw_rule(db, wk.id, "CIBIL >= 750")
    raw2 = _make_raw_rule(db, wk.id, "FOIR <= 50")
    db.commit()

    RuleExtractionService().extract_for_knowledge(db, wk.id)

    d1 = db.query(BusinessRuleDefinition).filter(
        BusinessRuleDefinition.workflow_business_rule_id == raw1.id
    ).first()
    d2 = db.query(BusinessRuleDefinition).filter(
        BusinessRuleDefinition.workflow_business_rule_id == raw2.id
    ).first()

    chk("d1 links raw1", d1 is not None and d1.workflow_business_rule_id == raw1.id)
    chk("d2 links raw2", d2 is not None and d2.workflow_business_rule_id == raw2.id)
    chk("d1.source_workflow_knowledge_id = wk.id",
        d1 is not None and d1.source_workflow_knowledge_id == wk.id)
    chk("d2.source_workflow_knowledge_id = wk.id",
        d2 is not None and d2.source_workflow_knowledge_id == wk.id)
    db.close()


def test_workspace_scope_from_persisted_knowledge():
    print("\n[3] scope_workspace_id comes from persisted WorkflowKnowledge, not caller")
    from app.rbac.rule_extractor import RuleExtractionService
    from app.models.business_rule_definition import BusinessRuleDefinition
    db = _session(); _seed(db, workspace_id=5)
    wk = _make_knowledge(db, workspace_id=5)
    _make_raw_rule(db, wk.id, "Interest rate <= 12")
    db.commit()

    # Pass only knowledge_id — workspace not separately provided
    result = RuleExtractionService().extract_for_knowledge(db, wk.id)

    chk("returned workspace_id = 5", result["workspace_id"] == 5)
    defn = db.query(BusinessRuleDefinition).filter(
        BusinessRuleDefinition.source_workflow_knowledge_id == wk.id
    ).first()
    chk("definition scope_workspace_id = 5",
        defn is not None and defn.scope_workspace_id == 5)
    db.close()


def test_idempotent_repeated_execution():
    print("\n[4] Repeated execution does not create duplicate definitions")
    from app.rbac.rule_extractor import RuleExtractionService
    from app.models.business_rule_definition import BusinessRuleDefinition
    db = _session(); _seed(db)
    wk = _make_knowledge(db, workspace_id=1)
    _make_raw_rule(db, wk.id, "Min CIBIL >= 700")
    db.commit()

    svc = RuleExtractionService()
    r1 = svc.extract_for_knowledge(db, wk.id)
    r2 = svc.extract_for_knowledge(db, wk.id)
    r3 = svc.extract_for_knowledge(db, wk.id)

    chk("first run: 1 created", r1["rules_created"] == 1)
    chk("second run: 0 created, 1 skipped",
        r2["rules_created"] == 0 and r2["rules_skipped"] == 1)
    chk("third run: 0 created, 1 skipped",
        r3["rules_created"] == 0 and r3["rules_skipped"] == 1)

    total = db.query(BusinessRuleDefinition).filter(
        BusinessRuleDefinition.source_workflow_knowledge_id == wk.id
    ).count()
    chk("exactly 1 definition in DB", total == 1)
    db.close()


def test_identical_descriptions_separate_provenance():
    print("\n[5] Two distinct raw rules with identical text retain separate provenance")
    from app.rbac.rule_extractor import RuleExtractionService
    from app.models.business_rule_definition import BusinessRuleDefinition
    db = _session(); _seed(db)
    # Two separate WorkflowKnowledge records (two BRDs) with the same rule text
    wk_a = _make_knowledge(db, workspace_id=1, workflow_name="HDFC BRD")
    wk_b = _make_knowledge(db, workspace_id=1, workflow_name="Axis BRD")
    raw_a = _make_raw_rule(db, wk_a.id, "CIBIL score must be >= 700")
    raw_b = _make_raw_rule(db, wk_b.id, "CIBIL score must be >= 700")
    db.commit()

    svc = RuleExtractionService()
    svc.extract_for_knowledge(db, wk_a.id)
    svc.extract_for_knowledge(db, wk_b.id)

    d_a = db.query(BusinessRuleDefinition).filter(
        BusinessRuleDefinition.workflow_business_rule_id == raw_a.id
    ).first()
    d_b = db.query(BusinessRuleDefinition).filter(
        BusinessRuleDefinition.workflow_business_rule_id == raw_b.id
    ).first()

    chk("separate definition for raw_a", d_a is not None)
    chk("separate definition for raw_b", d_b is not None)
    chk("d_a and d_b are different rows",
        d_a is not None and d_b is not None and d_a.id != d_b.id)
    chk("d_a links raw_a", d_a is not None and d_a.workflow_business_rule_id == raw_a.id)
    chk("d_b links raw_b", d_b is not None and d_b.workflow_business_rule_id == raw_b.id)
    chk("d_a source knowledge = wk_a",
        d_a is not None and d_a.source_workflow_knowledge_id == wk_a.id)
    chk("d_b source knowledge = wk_b",
        d_b is not None and d_b.source_workflow_knowledge_id == wk_b.id)
    db.close()


def test_knowledge_with_no_rules():
    print("\n[6] Knowledge with no raw rules handled safely — returns zeros")
    from app.rbac.rule_extractor import RuleExtractionService
    db = _session(); _seed(db)
    wk = _make_knowledge(db, workspace_id=1)
    db.commit()  # no raw rules added

    svc = RuleExtractionService()
    result = svc.extract_for_knowledge(db, wk.id)

    chk("rules_created = 0", result["rules_created"] == 0)
    chk("rules_skipped = 0", result["rules_skipped"] == 0)
    chk("workflow_knowledge_id returned", result["workflow_knowledge_id"] == wk.id)
    db.close()


def test_unknown_knowledge_id_raises():
    print("\n[7] Unknown WorkflowKnowledge ID raises ValueError")
    from app.rbac.rule_extractor import RuleExtractionService
    db = _session(); _seed(db)

    svc = RuleExtractionService()
    raised = False
    try:
        svc.extract_for_knowledge(db, workflow_knowledge_id=99999)
    except ValueError as exc:
        raised = True
        chk("ValueError message mentions ID",
            "99999" in str(exc), str(exc))
    chk("ValueError raised for unknown ID", raised)
    db.close()


def test_description_and_role_in_definition():
    print("\n[8] Description and allowed_roles populated correctly")
    from app.rbac.rule_extractor import RuleExtractionService
    from app.models.business_rule_definition import BusinessRuleDefinition
    from app.models.workflow_actor import WorkflowActor
    db = _session(); _seed(db)
    wk = _make_knowledge(db, workspace_id=1)
    raw = _make_raw_rule(db, wk.id, "Loan amount above Rs 5 lakh requires Branch Manager approval")
    # Add an actor so allowed_roles is populated
    db.add(WorkflowActor(workflow_knowledge_id=wk.id,
                         name="Branch Manager", role="approver"))
    db.commit()

    RuleExtractionService().extract_for_knowledge(db, wk.id)

    defn = db.query(BusinessRuleDefinition).filter(
        BusinessRuleDefinition.workflow_business_rule_id == raw.id
    ).first()
    chk("definition created", defn is not None)
    chk("description = rule text",
        defn is not None and defn.description == raw.rule)
    chk("active = True", defn is not None and defn.active is True)
    chk("allowed_roles populated",
        defn is not None and isinstance(defn.allowed_roles, list)
        and len(defn.allowed_roles) > 0)
    db.close()


def test_non_evaluable_rule_created_with_nulls():
    print("\n[9] Non-evaluable rule (no numeric threshold) has field=None, op=None, value=None")
    from app.rbac.rule_extractor import RuleExtractionService
    from app.models.business_rule_definition import BusinessRuleDefinition
    db = _session(); _seed(db)
    wk = _make_knowledge(db, workspace_id=1)
    raw = _make_raw_rule(db, wk.id,
                         "Applicant must provide Form 16 or last 2 years ITR")
    db.commit()

    RuleExtractionService().extract_for_knowledge(db, wk.id)

    defn = db.query(BusinessRuleDefinition).filter(
        BusinessRuleDefinition.workflow_business_rule_id == raw.id
    ).first()
    chk("definition created", defn is not None)
    chk("field is None (non-evaluable)", defn is not None and defn.field is None)
    chk("op is None",    defn is not None and defn.op is None)
    chk("value is None", defn is not None and defn.value is None)
    chk("active = True (non-evaluable rules are still active)",
        defn is not None and defn.active is True)
    db.close()


def test_extract_for_workspace_still_works():
    print("\n[10] extract_for_workspace() backward compatibility preserved")
    from app.rbac.rule_extractor import RuleExtractionService
    from app.models.business_rule_definition import BusinessRuleDefinition
    db = _session(); _seed(db)
    wk = _make_knowledge(db, workspace_id=1)
    _make_raw_rule(db, wk.id, "CIBIL >= 700")
    db.commit()

    # Old method still works
    result = RuleExtractionService().extract_for_workspace(db, workspace_id=1)
    chk("extract_for_workspace creates rules", result["rules_created"] >= 1)
    total = db.query(BusinessRuleDefinition).count()
    chk("at least 1 definition in DB", total >= 1)
    db.close()


# ── Runner ────────────────────────────────────────────────────────────────────

def main() -> int:
    print("=" * 60)
    print("RuleExtractionService.extract_for_knowledge() — Tests")
    print("=" * 60)
    for t in [
        test_only_rules_for_requested_knowledge_processed,
        test_definitions_link_exact_raw_rule,
        test_workspace_scope_from_persisted_knowledge,
        test_idempotent_repeated_execution,
        test_identical_descriptions_separate_provenance,
        test_knowledge_with_no_rules,
        test_unknown_knowledge_id_raises,
        test_description_and_role_in_definition,
        test_non_evaluable_rule_created_with_nulls,
        test_extract_for_workspace_still_works,
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
