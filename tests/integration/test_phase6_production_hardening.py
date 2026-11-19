"""
tests/integration/test_phase6_production_hardening.py

Phase 6 — RAG Production Hardening Integration Tests

Tests for embedding consistency, document versioning, retry/recovery,
concurrency safety, and retrieval consistency.
"""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.workspace import Workspace
from app.models.action_definitions import ActionDefinition
from app.models.trigger_definitions import TriggerDefinition
from app.models.workflow_business_rule import WorkflowBusinessRule
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.brd_document import BRDDocument, IngestionStatus
from app.models.document_version import DocumentVersion, VersionStatus
from app.models.ingestion_attempt import IngestionAttempt, AttemptStatus

from app.semantic.embedding_consistency import (
    EmbeddingConsistencyCheck,
    BackfillIdempotency,
    StaleEmbeddingDetection,
)
from app.knowledge_ingestions.document_version_manager import (
    DocumentVersionManager,
    ProvenanceValidator,
)
from app.knowledge_ingestions.attempt_recovery import AttemptRecoveryManager
from app.knowledge_ingestions.concurrency_safety import (
    ConcurrentRegistrationHandler,
    RunningAttemptGuard,
    WorkspaceBackfillLock,
)


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def session():
    """Fresh database session for each test."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def test_tenant(session: Session):
    """Create a test tenant."""
    tenant = Tenant(
        name="test_tenant",
        slug="test-tenant",
        display_name="Test Tenant",
    )
    session.add(tenant)
    session.commit()
    return tenant


@pytest.fixture
def test_workspace(session: Session, test_tenant: Tenant):
    """Create a test workspace."""
    workspace = Workspace(
        name="test_workspace",
        display_name="Test Workspace",
        tenant_id=test_tenant.id,
    )
    session.add(workspace)
    session.commit()
    return workspace


@pytest.fixture
def test_brd_document(session: Session, test_workspace: Workspace, test_tenant: Tenant):
    """Create a test BRD document."""
    doc = BRDDocument(
        tenant_id=test_tenant.id,
        workspace_id=test_workspace.id,
        original_filename="test_brd.pdf",
        sha256_hash="abc123def456",
        ingestion_status=IngestionStatus.REGISTERED.value,
    )
    session.add(doc)
    session.commit()
    return doc


# ──────────────────────────────────────────────────────────────────────────────
# Step 1: Embedding Consistency Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestEmbeddingConsistency:
    """Test embedding consistency checks and recovery."""

    def test_dimension_validation_accepts_valid_embedding(self):
        """Valid embedding (384 dims) passes validation."""
        embedding = [0.1] * 384
        # Should not raise
        EmbeddingConsistencyCheck.validate_embedding_dimension(embedding)

    def test_dimension_validation_rejects_invalid_embedding(self):
        """Invalid embedding (wrong dimension) raises ValueError."""
        embedding = [0.1] * 768  # Wrong dimension
        with pytest.raises(ValueError, match="dimension mismatch"):
            EmbeddingConsistencyCheck.validate_embedding_dimension(embedding)

    def test_dimension_validation_rejects_none(self):
        """None embedding raises ValueError."""
        with pytest.raises(ValueError, match="cannot be None"):
            EmbeddingConsistencyCheck.validate_embedding_dimension(None)

    def test_entity_embeddings_count_nulls(self, session: Session, test_workspace: Workspace):
        """Count NULL embeddings in workspace."""
        # Create action with embedding
        action_with = ActionDefinition(
            name="action_with_embedding",
            embedding=[0.1] * 384,
            embedding_model_name="BAAI/bge-small-en-v1.5",
            embedding_model_version="1.5",
        )
        # Create action without embedding
        action_without = ActionDefinition(
            name="action_without_embedding",
            embedding=None,
        )
        session.add_all([action_with, action_without])
        session.commit()

        stats = EmbeddingConsistencyCheck.validate_entity_embeddings(
            session, "action"
        )

        assert stats["total"] == 2
        assert stats["with_embedding"] == 1
        assert stats["without_embedding"] == 1

    def test_stale_embedding_detection(self, session: Session):
        """Detect embeddings from old model version."""
        # Create action with stale model
        action = ActionDefinition(
            name="action_stale",
            embedding=[0.1] * 384,
            embedding_model_name="old-model",
            embedding_model_version="1.0",
        )
        session.add(action)
        session.commit()

        stats = StaleEmbeddingDetection.find_stale_embeddings(
            session, "action", current_model_name="BAAI/bge-small-en-v1.5"
        )

        assert stats["stale_model_version"] > 0
        assert stats["total_stale"] > 0


class TestBackfillIdempotency:
    """Test backfill transaction isolation."""

    def test_backfill_batch_commits_all_or_nothing(self, session: Session):
        """Batch update is atomic: all commit or all rollback."""
        action1 = ActionDefinition(name="action1", embedding=None)
        action2 = ActionDefinition(name="action2", embedding=None)
        session.add_all([action1, action2])
        session.flush()

        records = [(action1.id, action1), (action2.id, action2)]
        embeddings = [[0.1] * 384, [0.2] * 384]

        # Should succeed
        updated, failed, failed_ids = BackfillIdempotency.backfill_batch_transactional(
            session,
            records,
            embeddings,
            "BAAI/bge-small-en-v1.5",
            "1.5",
            ActionDefinition,
        )

        assert updated == 2
        assert failed == 0
        assert action1.embedding is not None
        assert action2.embedding is not None

    def test_backfill_batch_rollback_on_invalid_dimension(self, session: Session):
        """Batch rolls back if any embedding has invalid dimension."""
        action1 = ActionDefinition(name="action1", embedding=None)
        action2 = ActionDefinition(name="action2", embedding=None)
        session.add_all([action1, action2])
        session.flush()

        records = [(action1.id, action1), (action2.id, action2)]
        embeddings = [[0.1] * 384, [0.2] * 768]  # Second embedding is wrong dimension

        # Should rollback and return failure
        updated, failed, failed_ids = BackfillIdempotency.backfill_batch_transactional(
            session,
            records,
            embeddings,
            "BAAI/bge-small-en-v1.5",
            "1.5",
            ActionDefinition,
        )

        assert updated == 0
        assert failed > 0
        # Embeddings should NOT have been updated
        session.refresh(action1)
        assert action1.embedding is None


# ──────────────────────────────────────────────────────────────────────────────
# Step 2: Document Version Consistency Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestDocumentVersionConsistency:
    """Test document versioning and provenance."""

    def test_get_active_document_version(
        self, session: Session, test_brd_document: BRDDocument
    ):
        """Get active (latest completed) version."""
        # Create version 1 as COMPLETED
        v1 = DocumentVersion(
            document_id=test_brd_document.id,
            version_number=1,
            sha256_hash="hash1",
            status=VersionStatus.COMPLETED.value,
            original_filename="test_v1.pdf",
        )
        # Create version 2 as PROCESSING (not active yet)
        v2 = DocumentVersion(
            document_id=test_brd_document.id,
            version_number=2,
            sha256_hash="hash2",
            status=VersionStatus.PROCESSING.value,
            original_filename="test_v2.pdf",
        )
        session.add_all([v1, v2])
        session.commit()

        active = DocumentVersionManager.get_active_document_version(
            session, test_brd_document.id
        )

        assert active.id == v1.id
        assert active.version_number == 1

    def test_duplicate_knowledge_detection(
        self, session: Session, test_workspace: Workspace
    ):
        """Detect duplicate WorkflowKnowledge for same version."""
        dv = DocumentVersion(
            document_id=1,
            version_number=1,
            sha256_hash="hash",
            original_filename="test.pdf",
        )
        session.add(dv)
        session.flush()

        # Create first WorkflowKnowledge
        wk1 = WorkflowKnowledge(
            workflow_name="workflow1",
            workspace_id=test_workspace.id,
            document_version_id=dv.id,
        )
        session.add(wk1)
        session.commit()

        # Should detect duplicate
        is_dup = DocumentVersionManager.is_duplicate_knowledge(session, dv.id)
        assert is_dup

    def test_provenance_validation_valid_chain(
        self,
        session: Session,
        test_brd_document: BRDDocument,
        test_workspace: Workspace,
        test_tenant: Tenant,
    ):
        """Validate complete provenance chain."""
        # Create knowledge linked to document
        knowledge = WorkflowKnowledge(
            workflow_name="test_workflow",
            workspace_id=test_workspace.id,
            brd_document_id=test_brd_document.id,
        )
        session.add(knowledge)
        session.flush()

        # Create rule linked to knowledge and document
        rule = WorkflowBusinessRule(
            workflow_knowledge_id=knowledge.id,
            rule="test rule",
            source_brd_document_id=test_brd_document.id,
        )
        session.add(rule)
        session.commit()

        # Validate
        is_valid = DocumentVersionManager.validate_provenance_chain(
            session, rule.id, test_workspace.id, test_tenant.id
        )
        assert is_valid

    def test_provenance_validation_null_source(
        self, session: Session, test_workspace: Workspace, test_tenant: Tenant
    ):
        """Detect NULL source_brd_document_id in rule."""
        knowledge = WorkflowKnowledge(
            workflow_name="test_workflow",
            workspace_id=test_workspace.id,
        )
        session.add(knowledge)
        session.flush()

        rule = WorkflowBusinessRule(
            workflow_knowledge_id=knowledge.id,
            rule="test rule",
            source_brd_document_id=None,  # NULL provenance
        )
        session.add(rule)
        session.commit()

        is_valid = DocumentVersionManager.validate_provenance_chain(
            session, rule.id, test_workspace.id, test_tenant.id
        )
        assert not is_valid


class TestProvenanceValidator:
    """Test workspace-wide provenance validation."""

    def test_validate_workspace_provenance(
        self,
        session: Session,
        test_workspace: Workspace,
        test_tenant: Tenant,
        test_brd_document: BRDDocument,
    ):
        """Validate all rules in workspace have valid provenance."""
        # Create knowledge and rules
        knowledge = WorkflowKnowledge(
            workflow_name="test_workflow",
            workspace_id=test_workspace.id,
            brd_document_id=test_brd_document.id,
        )
        session.add(knowledge)
        session.flush()

        # Rule with provenance
        rule_with = WorkflowBusinessRule(
            workflow_knowledge_id=knowledge.id,
            rule="rule with provenance",
            source_brd_document_id=test_brd_document.id,
        )

        # Rule without provenance
        rule_without = WorkflowBusinessRule(
            workflow_knowledge_id=knowledge.id,
            rule="rule without provenance",
            source_brd_document_id=None,
        )

        session.add_all([rule_with, rule_without])
        session.commit()

        stats = ProvenanceValidator.validate_workspace_wide(session, test_workspace.id)

        assert stats["total_rules"] == 2
        assert stats["rules_with_provenance"] == 1
        assert stats["rules_missing_provenance"] == 1


# ──────────────────────────────────────────────────────────────────────────────
# Step 3: Retry & Recovery Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestAttemptRecovery:
    """Test stale attempt detection and recovery."""

    def test_detect_stale_running_attempt(
        self, session: Session, test_workspace: Workspace, test_brd_document: BRDDocument
    ):
        """Detect RUNNING attempt older than TTL."""
        dv = DocumentVersion(
            document_id=test_brd_document.id,
            version_number=1,
            sha256_hash="hash",
            original_filename="test.pdf",
        )
        session.add(dv)
        session.flush()

        # Create stale RUNNING attempt (2 hours old)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
        attempt = IngestionAttempt(
            document_version_id=dv.id,
            attempt_number=1,
            status=AttemptStatus.RUNNING.value,
            started_at=cutoff,
        )
        session.add(attempt)
        session.commit()

        stats = AttemptRecoveryManager.detect_and_recover_stale_attempts(
            session, ttl_seconds=3600
        )

        assert stats["stale_attempts_found"] == 1
        assert stats["attempts_recovered"] == 1

        # Verify attempt marked as FAILED
        session.refresh(attempt)
        assert attempt.status == AttemptStatus.FAILED.value
        assert attempt.error_code == "STALE_RUNNING_ATTEMPT"

    def test_get_retry_candidates(
        self,
        session: Session,
        test_workspace: Workspace,
        test_brd_document: BRDDocument,
    ):
        """Get failed attempts eligible for retry."""
        dv = DocumentVersion(
            document_id=test_brd_document.id,
            version_number=1,
            sha256_hash="hash",
            original_filename="test.pdf",
        )
        session.add(dv)
        session.flush()

        # Create failed attempts
        attempt1 = IngestionAttempt(
            document_version_id=dv.id,
            attempt_number=1,
            status=AttemptStatus.FAILED.value,
            error_code="EXTRACTION_FAILED",
            completed_at=datetime.now(timezone.utc),
        )
        attempt2 = IngestionAttempt(
            document_version_id=dv.id,
            attempt_number=2,
            status=AttemptStatus.FAILED.value,
            error_code="LLM_TIMEOUT",
            completed_at=datetime.now(timezone.utc),
        )
        session.add_all([attempt1, attempt2])
        session.commit()

        candidates = AttemptRecoveryManager.get_retry_candidates(
            session, test_workspace.id
        )

        assert len(candidates) >= 2


# ──────────────────────────────────────────────────────────────────────────────
# Step 4: Concurrency Safety Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestConcurrencysafety:
    """Test concurrency and transaction safety."""

    def test_concurrent_registration_duplicate_handling(
        self, session: Session, test_workspace: Workspace
    ):
        """Handle concurrent duplicate registration gracefully."""
        workspace_id = test_workspace.id
        sha256_hash = "abc123"

        # First registration
        doc_id_1, is_new_1 = ConcurrentRegistrationHandler.register_or_get_existing(
            session, workspace_id, sha256_hash
        )
        assert is_new_1 is False  # No document created yet, just checked

        # Second registration (duplicate)
        doc_id_2, is_new_2 = ConcurrentRegistrationHandler.register_or_get_existing(
            session, workspace_id, sha256_hash
        )
        assert is_new_2 is False  # Still indicates duplicate

    def test_running_attempt_guard_prevents_duplicate(
        self, session: Session, test_brd_document: BRDDocument
    ):
        """Guard prevents two RUNNING attempts on same version."""
        dv = DocumentVersion(
            document_id=test_brd_document.id,
            version_number=1,
            sha256_hash="hash",
            original_filename="test.pdf",
        )
        session.add(dv)
        session.flush()

        # First attempt succeeds
        guard1 = RunningAttemptGuard.acquire_running_attempt(
            session, dv.id, attempt_number=1
        )
        assert guard1

        # Second attempt fails (one already running)
        guard2 = RunningAttemptGuard.acquire_running_attempt(
            session, dv.id, attempt_number=2
        )
        assert not guard2

    def test_workspace_backfill_lock(self):
        """Workspace backfill lock serializes backfills."""
        workspace_id = 123

        # Acquire lock
        acquired = WorkspaceBackfillLock.acquire_backfill_lock(workspace_id)
        assert acquired

        # Second acquire fails (lock held)
        acquired2 = WorkspaceBackfillLock.acquire_backfill_lock(workspace_id)
        assert not acquired2

        # Release and re-acquire
        WorkspaceBackfillLock.release_backfill_lock(workspace_id)
        acquired3 = WorkspaceBackfillLock.acquire_backfill_lock(workspace_id)
        assert acquired3

        WorkspaceBackfillLock.release_backfill_lock(workspace_id)


# ──────────────────────────────────────────────────────────────────────────────
# End of Tests
# ──────────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
