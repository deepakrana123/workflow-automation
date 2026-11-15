"""
scripts/test_rule_provenance.py

Tests for WorkflowBusinessRule.source_brd_document_id population.

Run from project root:
    .venv312\\Scripts\\python.exe scripts/test_rule_provenance.py
"""
from __future__ import annotations

import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv; load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
import app.models

failures: list[str] = []


# ── SQLite session with JSONB→JSON patch ──────────────────────────────────────

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


def _seed(db, t=1, w=1):
    from app.models.tenant import Tenant
    from app.models.workspace import Workspace
    db.add_all([
        Tenant(id=t, name=f"b{t}", slug=f"b-{t}", display_name=f"B{t}", active=True),
        Workspace(id=w, tenant_id=t, name="pl", display_name="PL", active=True),
    ])
    db.commit()


def _mock_extraction(rule_texts: list[str], workflow_name: str = "PL Workflow"):
    """Return a WorkflowExtraction mock with the given rule texts."""
    from app.knowledge_ingestions.schemas import WorkflowExtraction
    we = MagicMock(spec=WorkflowExtraction)
    we.workflow_name = workflow_name
    we.summary = "Test"
    we.triggers = []
    we.actors = []
    we.external_systems = []
    we.assumptions = []
    rules = []
    for text in rule_texts:
        r = MagicMock()
        r.rule = text
        r.condition = None
        r.outcome = None
        r.responsible_role = None
        r.threshold = None
        rules.append(r)
    we.business_rules = rules
    action = MagicMock()
    action.name = "approve_loan"
    action.description = "Approve loan"
    action.applicable_rules = []
    action.responsible_actors = []
    we.action_references = [action]
    return we


def _make_service(db, extraction):
    from app.knowledge_ingestions.service import KnowledgeIngestionService
    from app.knowledge_ingestions.workflow_repository import WorkflowRepository
    repo = WorkflowRepository(db)
    wf_ext = MagicMock()
    wf_ext.extract.return_value = extraction
    mapper = MagicMock()
    mapper.map_actions.return_value = None
    mapper.map_triggers.return_value = None
    return KnowledgeIngestionService(
        db=db,
        workflow_extractor=wf_ext,
        repository=repo,
        embedding_mapper=mapper,
    )


def chk(name: str, cond: bool, detail: str = "") -> None:
    icon = "✓" if cond else "✗"
    print(f"  {icon}  {name}" + (f"  — {detail}" if detail else ""))
    if not cond:
        failures.append(name)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_rules_receive_source_brd_document_id():
    print("\n[1] Rules created from BRD ingestion receive correct source_brd_document_id")
    from app.models.workflow_business_rule import WorkflowBusinessRule
    db = _session(); _seed(db)
    extraction = _mock_extraction(["CIBIL >= 700", "Loan amount <= 50 lakh"])
    svc = _make_service(db, extraction)
    wk = svc.ingest_from_text(
        "Eligibility rules.",
        workspace_id=1,
        brd_document_id=42,
    )
    rules = db.query(WorkflowBusinessRule).filter(
        WorkflowBusinessRule.workflow_knowledge_id == wk.id
    ).all()
    chk("2 rules created", len(rules) == 2)
    for r in rules:
        chk(
            f"rule '{r.rule[:30]}' has source_brd_document_id=42",
            r.source_brd_document_id == 42,
            str(r.source_brd_document_id),
        )
    db.close()


def test_multiple_rules_same_document_id():
    print("\n[2] Multiple rules from one knowledge row share the same source_brd_document_id")
    from app.models.workflow_business_rule import WorkflowBusinessRule
    db = _session(); _seed(db)
    rule_texts = [
        "Minimum CIBIL score 700",
        "FOIR must not exceed 50 percent",
        "Minimum employment tenure 2 years",
        "DPD = 0 for last 12 months",
    ]
    extraction = _mock_extraction(rule_texts)
    svc = _make_service(db, extraction)
    wk = svc.ingest_from_text("BRD rules.", workspace_id=1, brd_document_id=99)
    rules = db.query(WorkflowBusinessRule).filter(
        WorkflowBusinessRule.workflow_knowledge_id == wk.id
    ).all()
    chk("4 rules created", len(rules) == 4)
    ids = {r.source_brd_document_id for r in rules}
    chk("all rules have same source_brd_document_id", ids == {99}, str(ids))
    db.close()


def test_legacy_ingestion_null_source():
    print("\n[3] Legacy ingestion without brd_document_id keeps field NULL")
    from app.models.workflow_business_rule import WorkflowBusinessRule
    db = _session(); _seed(db)
    extraction = _mock_extraction(["Loan amount >= 100000"])
    svc = _make_service(db, extraction)
    wk = svc.ingest_from_text(
        "Legacy text.",
        workspace_id=1,
        brd_document_id=None,   # explicitly None
    )
    rules = db.query(WorkflowBusinessRule).filter(
        WorkflowBusinessRule.workflow_knowledge_id == wk.id
    ).all()
    chk("1 rule created", len(rules) == 1)
    chk("source_brd_document_id is NULL", rules[0].source_brd_document_id is None)
    db.close()


def test_brd_document_id_not_set_on_knowledge():
    print("\n[4] brd_document_id not passed → knowledge.brd_document_id also NULL")
    db = _session(); _seed(db)
    extraction = _mock_extraction(["Any rule"])
    svc = _make_service(db, extraction)
    wk = svc.ingest_from_text("Text.", workspace_id=1)
    chk("knowledge.brd_document_id is NULL", wk.brd_document_id is None)
    db.close()


def test_save_directly_with_brd_document_id():
    print("\n[5] WorkflowRepository.save() with explicit brd_document_id")
    from app.knowledge_ingestions.workflow_repository import WorkflowRepository
    from app.models.workflow_business_rule import WorkflowBusinessRule
    db = _session(); _seed(db)
    extraction = _mock_extraction(["Interest rate <= 12 percent"])
    repo = WorkflowRepository(db)
    wk = repo.save(extraction, workspace_id=1, source_document="test.pdf",
                   brd_document_id=77)
    db.commit()
    rules = db.query(WorkflowBusinessRule).filter(
        WorkflowBusinessRule.workflow_knowledge_id == wk.id
    ).all()
    chk("1 rule created", len(rules) == 1)
    chk("source_brd_document_id = 77", rules[0].source_brd_document_id == 77)
    db.close()


def test_save_directly_without_brd_document_id():
    print("\n[6] WorkflowRepository.save() without brd_document_id → NULL (backward compat)")
    from app.knowledge_ingestions.workflow_repository import WorkflowRepository
    from app.models.workflow_business_rule import WorkflowBusinessRule
    db = _session(); _seed(db)
    extraction = _mock_extraction(["Income > 30000"])
    repo = WorkflowRepository(db)
    wk = repo.save(extraction, workspace_id=1, source_document="old.pdf")
    db.commit()
    rules = db.query(WorkflowBusinessRule).filter(
        WorkflowBusinessRule.workflow_knowledge_id == wk.id
    ).all()
    chk("1 rule created", len(rules) == 1)
    chk("source_brd_document_id is NULL (backward compat)",
        rules[0].source_brd_document_id is None)
    db.close()


def test_other_rule_fields_unchanged():
    print("\n[7] Existing rule fields (rule, condition, outcome, responsible_role, threshold) unchanged")
    from app.knowledge_ingestions.workflow_repository import WorkflowRepository
    from app.models.workflow_business_rule import WorkflowBusinessRule
    db = _session(); _seed(db)
    from app.knowledge_ingestions.schemas import WorkflowExtraction
    we = MagicMock(spec=WorkflowExtraction)
    we.workflow_name = "Test"; we.summary = "s"
    we.triggers = []; we.actors = []; we.external_systems = []; we.assumptions = []
    r = MagicMock()
    r.rule = "CIBIL >= 700"
    r.condition = "Applicant is salaried"
    r.outcome = "Eligible for processing"
    r.responsible_role = "Credit Officer"
    r.threshold = "700"
    we.business_rules = [r]
    action = MagicMock()
    action.name = "approve"; action.description = "d"
    action.applicable_rules = []; action.responsible_actors = []
    we.action_references = [action]
    repo = WorkflowRepository(db)
    wk = repo.save(we, workspace_id=1, brd_document_id=5)
    db.commit()
    rule = db.query(WorkflowBusinessRule).filter(
        WorkflowBusinessRule.workflow_knowledge_id == wk.id
    ).first()
    chk("rule text correct",        rule.rule == "CIBIL >= 700")
    chk("condition correct",        rule.condition == "Applicant is salaried")
    chk("outcome correct",          rule.outcome == "Eligible for processing")
    chk("responsible_role correct", rule.responsible_role == "Credit Officer")
    chk("threshold correct",        rule.threshold == "700")
    chk("source_brd_document_id=5", rule.source_brd_document_id == 5)
    db.close()


def test_different_brd_documents_different_rules():
    print("\n[8] Two ingestions with different brd_document_ids produce isolated rules")
    from app.models.workflow_business_rule import WorkflowBusinessRule
    db = _session(); _seed(db)

    ext_a = _mock_extraction(["HDFC: CIBIL >= 750"], "HDFC PL")
    svc_a = _make_service(db, ext_a)
    wk_a = svc_a.ingest_from_text("HDFC rules.", workspace_id=1, brd_document_id=10)

    ext_b = _mock_extraction(["Axis: CIBIL >= 700"], "Axis PL")
    svc_b = _make_service(db, ext_b)
    wk_b = svc_b.ingest_from_text("Axis rules.", workspace_id=1, brd_document_id=20)

    rules_a = db.query(WorkflowBusinessRule).filter(
        WorkflowBusinessRule.workflow_knowledge_id == wk_a.id
    ).all()
    rules_b = db.query(WorkflowBusinessRule).filter(
        WorkflowBusinessRule.workflow_knowledge_id == wk_b.id
    ).all()

    chk("HDFC rule source = 10", all(r.source_brd_document_id == 10 for r in rules_a))
    chk("Axis rule source = 20", all(r.source_brd_document_id == 20 for r in rules_b))
    chk("no cross-contamination",
        not any(r.source_brd_document_id == 20 for r in rules_a) and
        not any(r.source_brd_document_id == 10 for r in rules_b))
    db.close()


# ── Runner ────────────────────────────────────────────────────────────────────

def main() -> int:
    print("=" * 60)
    print("Rule Provenance — source_brd_document_id population tests")
    print("=" * 60)
    for t in [
        test_rules_receive_source_brd_document_id,
        test_multiple_rules_same_document_id,
        test_legacy_ingestion_null_source,
        test_brd_document_id_not_set_on_knowledge,
        test_save_directly_with_brd_document_id,
        test_save_directly_without_brd_document_id,
        test_other_rule_fields_unchanged,
        test_different_brd_documents_different_rules,
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
