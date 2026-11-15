"""
scripts/test_knowledge_ingestion.py

Unit tests for KnowledgeIngestionService.ingest_from_text().
WorkflowExtractor and EmbeddingMapper are mocked — no LLM, no embeddings.

Run:
    .venv312\\Scripts\\python.exe scripts/test_knowledge_ingestion.py
"""
from __future__ import annotations
import sys, traceback
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


def _session():
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy import JSON
    for t in Base.metadata.tables.values():
        for c in t.columns:
            if isinstance(c.type, JSONB): c.type = JSON()
    e = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
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


def _mock_extraction(workflow_name="PL Workflow", actions=None, rules=None):
    """Return a WorkflowExtraction-like mock with the given structure."""
    from app.knowledge_ingestions.schemas import WorkflowExtraction
    we = MagicMock(spec=WorkflowExtraction)
    we.workflow_name = workflow_name
    we.summary = "Test summary"
    we.triggers = []
    we.business_rules = rules or []
    we.actors = []
    we.external_systems = []
    we.assumptions = []
    if actions is None:
        action = MagicMock(); action.name = "approve_loan"; action.description = "Approve loan"
        action.applicable_rules = []; action.responsible_actors = []
        we.action_references = [action]
    else:
        we.action_references = actions
    return we


def _make_service(db, extraction=None):
    from app.knowledge_ingestions.service import KnowledgeIngestionService
    from app.knowledge_ingestions.workflow_repository import WorkflowRepository
    repo = WorkflowRepository(db)
    wf_ext = MagicMock()
    wf_ext.extract.return_value = extraction or _mock_extraction()
    mapper = MagicMock()
    mapper.map_actions.return_value = None
    mapper.map_triggers.return_value = None
    svc = KnowledgeIngestionService(db=db, workflow_extractor=wf_ext,
                                     repository=repo, embedding_mapper=mapper)
    return svc


def chk(name, cond, detail=""):
    icon = "✓" if cond else "✗"
    print(f"  {icon}  {name}" + (f"  — {detail}" if detail else ""))
    if not cond: failures.append(name)


# ── tests ─────────────────────────────────────────────────────────────────────

def test_basic_ingest_from_text():
    print("\n[1] Basic ingest_from_text — creates WorkflowKnowledge")
    from app.models.workflow_knowledge import WorkflowKnowledge
    db = _session(); _seed(db)
    svc = _make_service(db)
    wk = svc.ingest_from_text("Loan eligibility rules.", workspace_id=1,
                               source_document="brd.pdf")
    chk("WorkflowKnowledge returned", wk is not None)
    chk("id assigned", wk.id is not None and wk.id > 0)
    chk("workspace_id = 1", wk.workspace_id == 1)
    chk("source_document set", wk.source_document == "brd.pdf")
    chk("1 row in DB", db.query(WorkflowKnowledge).count() == 1)
    db.close()


def test_brd_document_id_set():
    print("\n[2] brd_document_id populated on WorkflowKnowledge")
    db = _session(); _seed(db)
    svc = _make_service(db)
    wk = svc.ingest_from_text("text", workspace_id=1, brd_document_id=42)
    chk("brd_document_id = 42", wk.brd_document_id == 42)
    db.close()


def test_document_version_id_set():
    print("\n[3] document_version_id populated on WorkflowKnowledge")
    db = _session(); _seed(db)
    svc = _make_service(db)
    wk = svc.ingest_from_text("text", workspace_id=1, document_version_id=7)
    chk("document_version_id = 7", wk.document_version_id == 7)
    db.close()


def test_attempt_linked_in_same_commit():
    print("\n[4] ingestion_attempt updated in same commit as WorkflowKnowledge (T5+T6 merged)")
    from app.models.ingestion_attempt import AttemptStatus
    db = _session(); _seed(db)
    attempt = MagicMock()
    attempt.extracted_knowledge_id = None
    attempt.status = AttemptStatus.RUNNING.value
    attempt.completed_at = None
    svc = _make_service(db)
    wk = svc.ingest_from_text("text", workspace_id=1,
                               document_version_id=5, ingestion_attempt=attempt)
    chk("attempt.extracted_knowledge_id = wk.id", attempt.extracted_knowledge_id == wk.id)
    chk("attempt.status = COMPLETED", attempt.status == AttemptStatus.COMPLETED.value)
    chk("attempt.completed_at set", attempt.completed_at is not None)
    db.close()


def test_empty_text_raises():
    print("\n[5] Empty document_text raises WorkflowExtractionError")
    from app.knowledge_ingestions.exceptions import WorkflowExtractionError
    db = _session(); _seed(db)
    svc = _make_service(db)
    try:
        svc.ingest_from_text("   ", workspace_id=1)
        chk("error raised", False)
    except WorkflowExtractionError:
        chk("WorkflowExtractionError raised for empty text", True)
    db.close()


def test_no_actions_raises():
    print("\n[6] LLM extracts zero actions raises WorkflowExtractionError")
    from app.knowledge_ingestions.exceptions import WorkflowExtractionError
    db = _session(); _seed(db)
    empty_extraction = _mock_extraction(actions=[])
    svc = _make_service(db, extraction=empty_extraction)
    try:
        svc.ingest_from_text("some text", workspace_id=1)
        chk("error raised", False)
    except WorkflowExtractionError:
        chk("WorkflowExtractionError raised for no actions", True)
    db.close()


def test_ghost_knowledge_recovery():
    print("\n[7] Ghost-knowledge recovery: existing row returned, no duplicate")
    from app.models.workflow_knowledge import WorkflowKnowledge
    from app.models.ingestion_attempt import AttemptStatus
    db = _session(); _seed(db)
    svc = _make_service(db)

    # First call creates the row
    wk1 = svc.ingest_from_text("text", workspace_id=1, document_version_id=10)
    chk("first call created row", wk1.id is not None)

    # Second call with same document_version_id — ghost recovery
    attempt = MagicMock()
    attempt.extracted_knowledge_id = None
    attempt.status = AttemptStatus.RUNNING.value
    attempt.completed_at = None
    wk2 = svc.ingest_from_text("text", workspace_id=1,
                                document_version_id=10, ingestion_attempt=attempt)
    chk("same knowledge row returned", wk1.id == wk2.id)
    chk("no duplicate row", db.query(WorkflowKnowledge).count() == 1)
    chk("attempt linked to existing row", attempt.extracted_knowledge_id == wk1.id)
    chk("attempt COMPLETED", attempt.status == AttemptStatus.COMPLETED.value)
    db.close()


def test_child_rows_created():
    print("\n[8] WorkflowActionMapping rows created for each action")
    from app.models.workflow_action_mapping import WorkflowActionMapping
    from app.knowledge_ingestions.schemas import WorkflowExtraction
    db = _session(); _seed(db)
    a1 = MagicMock(); a1.name="action_a"; a1.description="a"; a1.applicable_rules=[]; a1.responsible_actors=[]
    a2 = MagicMock(); a2.name="action_b"; a2.description="b"; a2.applicable_rules=[]; a2.responsible_actors=[]
    t1 = MagicMock(); t1.name="trig_a"; t1.description="t"; t1.applicable_rules=[]; t1.responsible_actors=[]
    extraction = _mock_extraction(actions=[a1, a2])
    extraction.triggers = [t1]
    db2 = _session(); _seed(db2)
    svc = _make_service(db2, extraction=extraction)
    wk = svc.ingest_from_text("text", workspace_id=1)
    mappings = db2.query(WorkflowActionMapping).filter(
        WorkflowActionMapping.workflow_knowledge_id == wk.id
    ).all()
    chk("2 action mapping rows", len(mappings) == 2)
    names = {m.extract_name for m in mappings}
    chk("action names correct", names == {"action_a", "action_b"})
    db2.close()


def test_embedding_mapper_called_with_workspace_id():
    print("\n[9] EmbeddingMapper called with correct workspace_id")
    db = _session(); _seed(db)
    svc = _make_service(db)
    svc.ingest_from_text("text", workspace_id=1)
    svc.embedding_mapper.map_actions.assert_called_once_with(workspace_id=1)
    svc.embedding_mapper.map_triggers.assert_called_once_with(workspace_id=1)
    chk("map_actions called with workspace_id=1", True)
    chk("map_triggers called with workspace_id=1", True)
    db.close()


def test_rollback_on_persist_failure():
    print("\n[10] DB failure → rollback, RepositoryError raised")
    from app.knowledge_ingestions.exceptions import RepositoryError
    from app.models.workflow_knowledge import WorkflowKnowledge
    db = _session(); _seed(db)
    svc = _make_service(db)
    # Make the commit fail
    original_commit = db.commit
    call_count = [0]
    def failing_commit():
        call_count[0] += 1
        if call_count[0] == 1:
            raise Exception("DB error")
        return original_commit()
    db.commit = failing_commit
    try:
        svc.ingest_from_text("text", workspace_id=1)
        chk("RepositoryError raised", False)
    except RepositoryError:
        chk("RepositoryError raised", True)
    chk("no rows committed", db.query(WorkflowKnowledge).count() == 0)
    db.close()


def main():
    print("=" * 60)
    print("KnowledgeIngestionService — Unit Tests")
    print("=" * 60)
    for t in [
        test_basic_ingest_from_text, test_brd_document_id_set,
        test_document_version_id_set, test_attempt_linked_in_same_commit,
        test_empty_text_raises, test_no_actions_raises,
        test_ghost_knowledge_recovery, test_child_rows_created,
        test_embedding_mapper_called_with_workspace_id,
        test_rollback_on_persist_failure,
    ]:
        try: t()
        except Exception as e:
            print(f"  [UNEXPECTED] {e}"); traceback.print_exc(); failures.append(t.__name__)
    print("\n" + "=" * 60)
    if failures:
        print(f"FAILED — {len(failures)}: " + ", ".join(failures))
        return 1
    print("ALL TESTS PASSED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
