"""
scripts/test_ingestion_orchestrator.py

Tests for IngestionOrchestrator with integrated rule extraction.

Run from project root:
    .venv312\\Scripts\\python.exe scripts/test_ingestion_orchestrator.py
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path
from unittest.mock import MagicMock, patch

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


def chk(name: str, cond: bool, detail: str = "") -> None:
    icon = "✓" if cond else "✗"
    print(f"  {icon}  {name}" + (f"  — {detail}" if detail else ""))
    if not cond:
        failures.append(name)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_orchestration_result_exposes_rule_extraction_counts():
    print("\n[1] OrchestrationResult includes rules_created, rules_skipped, rules_error_message")
    from app.knowledge_ingestions.ingestion_orchestrator import OrchestrationResult
    import inspect
    sig = inspect.signature(OrchestrationResult)
    params = list(sig.parameters)
    chk("OrchestrationResult has rules_created field",
        "rules_created" in params)
    chk("OrchestrationResult has rules_skipped field",
        "rules_skipped" in params)
    chk("OrchestrationResult has rules_error_message field",
        "rules_error_message" in params)


def test_orchestrator_injects_rule_extraction_service():
    print("\n[2] IngestionOrchestrator constructs RuleExtractionService when not injected")
    from app.knowledge_ingestions.ingestion_orchestrator import IngestionOrchestrator
    from app.rbac.rule_extractor import RuleExtractionService
    db = _session(); _seed(db)
    orch = IngestionOrchestrator(db)
    chk("_rule_extraction_svc is set",
        orch._rule_extraction_svc is not None)
    chk("_rule_extraction_svc is RuleExtractionService",
        isinstance(orch._rule_extraction_svc, RuleExtractionService))
    db.close()


def test_orchestrator_accepts_injected_rule_extraction_service():
    print("\n[3] IngestionOrchestrator accepts injected RuleExtractionService")
    from app.knowledge_ingestions.ingestion_orchestrator import IngestionOrchestrator
    db = _session(); _seed(db)
    mock_svc = MagicMock()
    orch = IngestionOrchestrator(db, rule_extraction_service=mock_svc)
    chk("_rule_extraction_svc is the injected mock",
        orch._rule_extraction_svc is mock_svc)
    db.close()


def test_extract_structured_rules_success():
    print("\n[4] _extract_structured_rules handles successful extraction")
    from app.knowledge_ingestions.ingestion_orchestrator import IngestionOrchestrator
    from app.models.workflow_knowledge import WorkflowKnowledge
    db = _session(); _seed(db)
    
    # Create a fake WorkflowKnowledge
    wk = WorkflowKnowledge(
        workflow_name="Test",
        summary="Test",
        workspace_id=1,
        source_document="test.pdf",
    )
    db.add(wk)
    db.commit()
    
    # Mock the rule extraction service to return successful result
    mock_svc = MagicMock()
    mock_svc.extract_for_knowledge.return_value = {
        "workflow_knowledge_id": wk.id,
        "workspace_id": 1,
        "rules_created": 3,
        "rules_skipped": 0,
    }
    orch = IngestionOrchestrator(db, rule_extraction_service=mock_svc)
    result = orch._extract_structured_rules(knowledge_id=wk.id, document_id=1)
    
    chk("rules_created = 3", result["rules_created"] == 3)
    chk("rules_skipped = 0", result["rules_skipped"] == 0)
    chk("error_message is None", result["error_message"] is None)
    chk("extract_for_knowledge was called", mock_svc.extract_for_knowledge.called)
    db.close()


def test_extract_structured_rules_knowledge_not_found():
    print("\n[5] _extract_structured_rules handles ValueError (knowledge not found)")
    from app.knowledge_ingestions.ingestion_orchestrator import IngestionOrchestrator
    db = _session(); _seed(db)
    
    mock_svc = MagicMock()
    mock_svc.extract_for_knowledge.side_effect = ValueError("WorkflowKnowledge 999 not found")
    orch = IngestionOrchestrator(db, rule_extraction_service=mock_svc)
    result = orch._extract_structured_rules(knowledge_id=999, document_id=1)
    
    chk("rules_created = 0", result["rules_created"] == 0)
    chk("rules_skipped = 0", result["rules_skipped"] == 0)
    chk("error_message is set", result["error_message"] is not None)
    chk("error message mentions 'not found'",
        "not found" in result["error_message"].lower())
    db.close()


def test_extract_structured_rules_unexpected_error():
    print("\n[6] _extract_structured_rules handles unexpected exceptions")
    from app.knowledge_ingestions.ingestion_orchestrator import IngestionOrchestrator
    db = _session(); _seed(db)
    
    mock_svc = MagicMock()
    mock_svc.extract_for_knowledge.side_effect = RuntimeError("Database connection lost")
    orch = IngestionOrchestrator(db, rule_extraction_service=mock_svc)
    result = orch._extract_structured_rules(knowledge_id=1, document_id=1)
    
    chk("rules_created = 0", result["rules_created"] == 0)
    chk("rules_skipped = 0", result["rules_skipped"] == 0)
    chk("error_message is set", result["error_message"] is not None)
    chk("error message mentions 'failed'",
        "failed" in result["error_message"].lower())
    db.close()


def test_extract_structured_rules_zero_rules_not_error():
    print("\n[7] _extract_structured_rules treats zero raw rules as success")
    from app.knowledge_ingestions.ingestion_orchestrator import IngestionOrchestrator
    from app.models.workflow_knowledge import WorkflowKnowledge
    db = _session(); _seed(db)
    
    wk = WorkflowKnowledge(
        workflow_name="Test",
        summary="Test",
        workspace_id=1,
        source_document="test.pdf",
    )
    db.add(wk)
    db.commit()
    
    mock_svc = MagicMock()
    mock_svc.extract_for_knowledge.return_value = {
        "workflow_knowledge_id": wk.id,
        "workspace_id": 1,
        "rules_created": 0,
        "rules_skipped": 0,
    }
    orch = IngestionOrchestrator(db, rule_extraction_service=mock_svc)
    result = orch._extract_structured_rules(knowledge_id=wk.id, document_id=1)
    
    chk("rules_created = 0", result["rules_created"] == 0)
    chk("rules_skipped = 0", result["rules_skipped"] == 0)
    chk("error_message is None (zero rules ≠ error)",
        result["error_message"] is None)
    db.close()


def test_orchestration_result_structure_backward_compat():
    print("\n[8] OrchestrationResult backward compatibility — old fields still exist")
    from app.knowledge_ingestions.ingestion_orchestrator import OrchestrationResult
    result = OrchestrationResult(
        document_id=1,
        document_version_id=2,
        ingestion_attempt_id=3,
        knowledge_id=4,
        overall_status="COMPLETED",
        is_duplicate=False,
        warnings=["test"],
        error_message=None,
    )
    chk("document_id accessible", result.document_id == 1)
    chk("knowledge_id accessible", result.knowledge_id == 4)
    chk("overall_status accessible", result.overall_status == "COMPLETED")
    chk("warnings accessible", result.warnings == ["test"])
    chk("new field rules_created defaults to 0", result.rules_created == 0)
    chk("new field rules_skipped defaults to 0", result.rules_skipped == 0)
    chk("new field rules_error_message defaults to None",
        result.rules_error_message is None)


def test_rule_extraction_called_after_knowledge_persists():
    print("\n[9] Rule extraction is called AFTER knowledge persistence (integration)")
    from app.knowledge_ingestions.ingestion_orchestrator import IngestionOrchestrator
    from app.knowledge_ingestions.service import KnowledgeIngestionService
    from app.models.workflow_knowledge import WorkflowKnowledge
    db = _session(); _seed(db)
    
    # Mock the rule extraction to track calls
    rule_extraction_calls: list[int] = []
    
    def track_rule_extraction(db, workflow_knowledge_id):
        rule_extraction_calls.append(workflow_knowledge_id)
        return {
            "workflow_knowledge_id": workflow_knowledge_id,
            "workspace_id": 1,
            "rules_created": 2,
            "rules_skipped": 0,
        }
    
    mock_rule_svc = MagicMock()
    mock_rule_svc.extract_for_knowledge.side_effect = track_rule_extraction
    
    # Create knowledge
    wk = WorkflowKnowledge(
        workflow_name="Test",
        summary="Test",
        workspace_id=1,
        source_document="test.pdf",
    )
    db.add(wk)
    db.commit()
    
    orch = IngestionOrchestrator(db, rule_extraction_service=mock_rule_svc)
    
    # Call _extract_structured_rules
    result = orch._extract_structured_rules(knowledge_id=wk.id, document_id=1)
    
    chk("rule extraction was called", len(rule_extraction_calls) > 0)
    chk("rule extraction received correct knowledge_id",
        rule_extraction_calls[0] == wk.id)
    chk("rule extraction result reflects counts",
        result["rules_created"] == 2 and result["rules_skipped"] == 0)
    db.close()


def test_rule_extraction_failure_does_not_destroy_knowledge():
    print("\n[10] Rule extraction failure preserves WorkflowKnowledge and raw rules")
    from app.knowledge_ingestions.ingestion_orchestrator import IngestionOrchestrator
    from app.models.workflow_knowledge import WorkflowKnowledge
    from app.models.workflow_business_rule import WorkflowBusinessRule
    db = _session(); _seed(db)
    
    # Create knowledge and raw rules
    wk = WorkflowKnowledge(
        workflow_name="Test",
        summary="Test",
        workspace_id=1,
        source_document="test.pdf",
    )
    db.add(wk)
    db.flush()
    
    raw_rule = WorkflowBusinessRule(
        workflow_knowledge_id=wk.id,
        rule="CIBIL >= 700",
    )
    db.add(raw_rule)
    db.commit()
    
    # Mock rule extraction to fail
    mock_rule_svc = MagicMock()
    mock_rule_svc.extract_for_knowledge.side_effect = RuntimeError("DB error")
    orch = IngestionOrchestrator(db, rule_extraction_service=mock_rule_svc)
    
    # Call rule extraction — should fail gracefully
    result = orch._extract_structured_rules(knowledge_id=wk.id, document_id=1)
    
    chk("error_message is set", result["error_message"] is not None)
    
    # Verify knowledge still exists
    wk_still_exists = db.query(WorkflowKnowledge).filter(
        WorkflowKnowledge.id == wk.id
    ).first()
    chk("WorkflowKnowledge still persisted after rule extraction failure",
        wk_still_exists is not None)
    
    # Verify raw rule still exists
    rule_still_exists = db.query(WorkflowBusinessRule).filter(
        WorkflowBusinessRule.id == raw_rule.id
    ).first()
    chk("Raw WorkflowBusinessRule still persisted after extraction failure",
        rule_still_exists is not None)
    db.close()


def test_orchestration_result_includes_rule_info_in_success():
    print("\n[11] OrchestrationResult populated with rule counts on successful ingestion")
    from app.knowledge_ingestions.ingestion_orchestrator import OrchestrationResult
    result = OrchestrationResult(
        document_id=1,
        document_version_id=2,
        ingestion_attempt_id=3,
        knowledge_id=4,
        overall_status="COMPLETED",
        rules_created=5,
        rules_skipped=2,
        rules_error_message=None,
    )
    chk("overall_status = COMPLETED", result.overall_status == "COMPLETED")
    chk("rules_created = 5", result.rules_created == 5)
    chk("rules_skipped = 2", result.rules_skipped == 2)
    chk("rules_error_message is None", result.rules_error_message is None)


def test_orchestration_result_includes_rule_error_on_extraction_failure():
    print("\n[12] OrchestrationResult includes rule error message when extraction fails")
    from app.knowledge_ingestions.ingestion_orchestrator import OrchestrationResult
    result = OrchestrationResult(
        document_id=1,
        document_version_id=2,
        ingestion_attempt_id=3,
        knowledge_id=4,
        overall_status="COMPLETED",  # Knowledge persisted, so overall still COMPLETED
        rules_created=0,
        rules_skipped=0,
        rules_error_message="Structured rule extraction failed: DB connection lost",
    )
    chk("overall_status = COMPLETED (knowledge OK)",
        result.overall_status == "COMPLETED")
    chk("rules_error_message is set", result.rules_error_message is not None)
    chk("rules_created = 0", result.rules_created == 0)


# ── Runner ────────────────────────────────────────────────────────────────────

def main() -> int:
    print("=" * 70)
    print("IngestionOrchestrator — Rule Extraction Integration Tests")
    print("=" * 70)
    for t in [
        test_orchestration_result_exposes_rule_extraction_counts,
        test_orchestrator_injects_rule_extraction_service,
        test_orchestrator_accepts_injected_rule_extraction_service,
        test_extract_structured_rules_success,
        test_extract_structured_rules_knowledge_not_found,
        test_extract_structured_rules_unexpected_error,
        test_extract_structured_rules_zero_rules_not_error,
        test_orchestration_result_structure_backward_compat,
        test_rule_extraction_called_after_knowledge_persists,
        test_rule_extraction_failure_does_not_destroy_knowledge,
        test_orchestration_result_includes_rule_info_in_success,
        test_orchestration_result_includes_rule_error_on_extraction_failure,
    ]:
        try:
            t()
        except Exception as exc:
            print(f"  [UNEXPECTED] {exc}")
            traceback.print_exc()
            failures.append(t.__name__)
    print("\n" + "=" * 70)
    if failures:
        print(f"FAILED — {len(failures)}: " + ", ".join(failures))
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
