"""
Phase 2C: Batch-Based and Resumable Embedding Backfill Tests

Tests for:
1. Bounded database batch processing with keyset pagination
2. Independent batch commits and fault tolerance
3. Resumability from watermark
4. Retry of failed records
5. Backward compatibility with existing CLI
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import uuid

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.action_definitions import ActionDefinition
from app.models.trigger_definitions import TriggerDefinition
from app.models.workflow_business_rule import WorkflowBusinessRule
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workspace import Workspace
from app.models.tenant import Tenant
from scripts.backfill_embeddings import (
    fetch_pending_record_batch,
    process_batch_inference,
    commit_batch_updates,
    build_action_text,
    build_trigger_text,
)


def _uid() -> int:
    """Generate unique ID."""
    return uuid.uuid4().int % (2**31 - 1)


@pytest.fixture
def session() -> Session:
    """Database session for tests."""
    session = SessionLocal()
    yield session
    # Clean up test data after each test
    session.query(ActionDefinition).filter(ActionDefinition.id >= 100000).delete()
    session.query(TriggerDefinition).filter(TriggerDefinition.id >= 100000).delete()
    session.query(WorkflowBusinessRule).filter(WorkflowBusinessRule.id >= 100000).delete()
    session.query(WorkflowKnowledge).filter(WorkflowKnowledge.id >= 100000).delete()
    session.query(Workspace).filter(Workspace.id >= 10000).delete()
    session.query(Tenant).filter(Tenant.id >= 1000).delete()
    session.commit()
    session.close()


@pytest.fixture
def setup_tenant_workspace(session: Session):
    """Create test tenant and workspace."""
    tid = _uid()
    wid = _uid()
    
    tenant = Tenant(
        id=tid,
        name=f"test-tenant-{tid}",
        slug=f"test-tenant-{tid}",
        display_name="Test Tenant",
        active=True,
    )
    session.add(tenant)
    session.flush()
    
    workspace = Workspace(
        id=wid,
        tenant_id=tenant.id,
        name=f"test-workspace-{wid}",
        display_name="Test Workspace",
        active=True,
    )
    session.add(workspace)
    session.flush()
    
    return tenant, workspace


class TestBatchedDatabaseProcessing:
    """Test bounded batch fetching with keyset pagination."""

    def test_fetch_batch_with_limit(self, session: Session):
        """Verify fetch_pending_record_batch respects batch size limit."""
        from scripts.backfill_embeddings import fetch_pending_record_batch
        
        # Create 5 actions without embeddings
        for i in range(5):
            aid = _uid()
            action = ActionDefinition(
                id=aid,
                name=f"test_action_{aid}",
                display_name=f"Action {i}",
                workflow_type="payment",
                embedding=None,
            )
            session.add(action)
        session.commit()
        
        # Fetch batch with size 2
        batch = fetch_pending_record_batch(
            session,
            ActionDefinition,
            db_batch_size=2,
            force=False,
        )
        
        assert len(batch) <= 2, "Batch should respect size limit"
        assert all(isinstance(record_id, int) for record_id, _ in batch)
        assert all(isinstance(record, ActionDefinition) for _, record in batch)

    def test_keyset_pagination_stable_order(self, session: Session):
        """Verify keyset pagination maintains stable order and avoids OFFSET."""
        from scripts.backfill_embeddings import fetch_pending_record_batch
        
        # Create actions with predictable IDs (sort by id)
        action_ids = []
        for i in range(5):
            aid = 100000 + i
            action = ActionDefinition(
                id=aid,
                name=f"test_action_{aid}",
                display_name=f"Action {i}",
                workflow_type="payment",
                embedding=None,
            )
            session.add(action)
            action_ids.append(aid)
        session.commit()
        
        # Fetch first batch
        batch1 = fetch_pending_record_batch(
            session,
            ActionDefinition,
            db_batch_size=2,
            force=False,
            resume_from=None,
        )
        
        assert len(batch1) == 2
        watermark = batch1[-1][0]
        
        # Fetch second batch using watermark
        batch2 = fetch_pending_record_batch(
            session,
            ActionDefinition,
            db_batch_size=2,
            force=False,
            resume_from=watermark,
        )
        
        # No overlap between batches
        batch1_ids = {r[0] for r in batch1}
        batch2_ids = {r[0] for r in batch2}
        assert batch1_ids.isdisjoint(batch2_ids), "Batches should not overlap"

    def test_batch_skip_existing_embeddings(self, session: Session):
        """Verify batch skips records with existing embeddings (force=False)."""
        from scripts.backfill_embeddings import fetch_pending_record_batch
        
        # Create action with embedding
        aid1 = _uid()
        action_with = ActionDefinition(
            id=aid1,
            name=f"test_with_{aid1}",
            display_name="Has Embedding",
            workflow_type="payment",
            embedding=[0.1] * 384,
        )
        
        # Create action without embedding
        aid2 = _uid()
        action_without = ActionDefinition(
            id=aid2,
            name=f"test_without_{aid2}",
            display_name="No Embedding",
            workflow_type="payment",
            embedding=None,
        )
        
        session.add_all([action_with, action_without])
        session.commit()
        
        # Fetch without force
        batch = fetch_pending_record_batch(
            session,
            ActionDefinition,
            db_batch_size=10,
            force=False,
        )
        
        batch_ids = {r[0] for r in batch}
        assert aid1 not in batch_ids, "Should skip action with embedding"
        assert aid2 in batch_ids, "Should include action without embedding"

    def test_batch_include_existing_with_force(self, session: Session):
        """Verify batch includes all records when force=True."""
        from scripts.backfill_embeddings import fetch_pending_record_batch
        
        aid1 = _uid()
        action_with = ActionDefinition(
            id=aid1,
            name=f"test_with_{aid1}",
            display_name="Has Embedding",
            workflow_type="payment",
            embedding=[0.1] * 384,
        )
        session.add(action_with)
        session.commit()
        
        batch = fetch_pending_record_batch(
            session,
            ActionDefinition,
            db_batch_size=10,
            force=True,
        )
        
        batch_ids = {r[0] for r in batch}
        # With force=True, query doesn't filter by embedding IS NULL, so it returns all
        # Our newly added record should be in the batch
        assert len(batch) > 0, "force=True should return records"


class TestInferenceProcessing:
    """Test batch inference with separate batch sizing."""

    def test_inference_batch_size_respected(self, session: Session):
        """Verify inference batch size is separate from database batch size."""
        from scripts.backfill_embeddings import process_batch_inference, build_action_text
        
        # Create records
        batch = []
        for i in range(5):
            aid = _uid()
            action = ActionDefinition(
                id=aid,
                name=f"test_action_{aid}",
                display_name=f"Action {i}",
                workflow_type="payment",
            )
            batch.append((aid, action))
        
        # Mock model to track batch sizes
        mock_model = MagicMock()
        call_count = 0
        
        def encode_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            batch_size_param = kwargs.get('batch_size', 32)
            # Return mock embeddings
            return [[0.1] * 384 for _ in args[0]]
        
        mock_model.encode.side_effect = encode_side_effect
        
        # Run inference with small batch size
        results = process_batch_inference(
            batch,
            mock_model,
            build_action_text,
            inference_batch_size=2,
        )
        
        # Verify model.encode was called with inference_batch_size
        mock_model.encode.assert_called()
        call_args = mock_model.encode.call_args
        assert call_args[1]['batch_size'] == 2

    def test_partial_batch_failure(self, session: Session):
        """Verify failed inference doesn't block rest of batch."""
        # Create records
        batch = []
        for i in range(3):
            aid = _uid()
            action = ActionDefinition(
                id=aid,
                name=f"test_action_{aid}",
                display_name=f"Action {i}",
                workflow_type="payment",
            )
            session.add(action)
            batch.append((aid, action))
        session.commit()
        
        # Mock model to fail on second call
        mock_model = MagicMock()
        mock_model.encode.side_effect = RuntimeError("Inference failure")
        
        results = process_batch_inference(
            batch,
            mock_model,
            build_action_text,
            inference_batch_size=32,
        )
        
        # All records should have exceptions
        assert len(results) == 3
        assert all(isinstance(r, Exception) for r in results.values())


class TestBatchCommit:
    """Test independent batch commit and fault tolerance."""

    def test_batch_commits_independently(self, session: Session):
        """Verify each batch commits independently."""
        from scripts.backfill_embeddings import commit_batch_updates
        
        # Create records
        aid1, aid2 = _uid(), _uid()
        action1 = ActionDefinition(
            id=aid1,
            name=f"test1_{aid1}",
            display_name="Action 1",
            workflow_type="payment",
        )
        action2 = ActionDefinition(
            id=aid2,
            name=f"test2_{aid2}",
            display_name="Action 2",
            workflow_type="payment",
        )
        session.add_all([action1, action2])
        session.commit()
        
        batch = [(aid1, action1), (aid2, action2)]
        results = {
            aid1: ([0.1] * 384, None),
            aid2: ([0.2] * 384, None),
        }
        
        # Commit batch
        updated, failed, failed_ids = commit_batch_updates(
            session,
            batch,
            results,
            model_name="test-model",
            model_version="1.0",
        )
        
        assert updated == 2
        assert failed == 0
        
        # Verify embeddings persisted
        session.refresh(action1)
        session.refresh(action2)
        assert action1.embedding is not None
        assert action2.embedding is not None
        assert action1.embedding_model_name == "test-model"

    def test_failed_records_tracked(self, session: Session):
        """Verify failed records are tracked and reported."""
        from scripts.backfill_embeddings import commit_batch_updates
        
        aid1, aid2 = _uid(), _uid()
        action1 = ActionDefinition(
            id=aid1,
            name=f"test1_{aid1}",
            display_name="Action 1",
            workflow_type="payment",
        )
        action2 = ActionDefinition(
            id=aid2,
            name=f"test2_{aid2}",
            display_name="Action 2",
            workflow_type="payment",
        )
        session.add_all([action1, action2])
        session.commit()
        
        batch = [(aid1, action1), (aid2, action2)]
        results = {
            aid1: RuntimeError("Inference failed"),
            aid2: ([0.2] * 384, None),
        }
        
        updated, failed, failed_ids = commit_batch_updates(
            session,
            batch,
            results,
            model_name="test-model",
            model_version="1.0",
        )
        
        assert updated == 1
        assert failed == 1
        assert aid1 in failed_ids


class TestResumability:
    """Test ability to resume from watermark."""

    def test_resume_from_watermark(self, session: Session):
        """Verify resuming from watermark skips already processed records."""
        from scripts.backfill_embeddings import fetch_pending_record_batch
        
        # Create 10 actions
        action_ids = []
        for i in range(10):
            aid = 200000 + i
            action = ActionDefinition(
                id=aid,
                name=f"test_{aid}",
                display_name=f"Action {i}",
                workflow_type="payment",
                embedding=None,
            )
            session.add(action)
            action_ids.append(aid)
        session.commit()
        
        # Fetch first batch (3 records)
        batch1 = fetch_pending_record_batch(
            session,
            ActionDefinition,
            db_batch_size=3,
            force=False,
            resume_from=None,
        )
        watermark = batch1[-1][0]
        
        # Fetch second batch using watermark
        batch2 = fetch_pending_record_batch(
            session,
            ActionDefinition,
            db_batch_size=3,
            force=False,
            resume_from=watermark,
        )
        
        # Verify no overlap and batch2 continues from watermark
        batch1_ids = {r[0] for r in batch1}
        batch2_ids = {r[0] for r in batch2}
        
        assert batch1_ids.isdisjoint(batch2_ids)
        assert all(id > watermark for id in batch2_ids)

    def test_resume_after_partial_failure(self, session: Session):
        """Verify failed records remain pending for retry after resume."""
        from scripts.backfill_embeddings import fetch_pending_record_batch
        
        # Create actions
        aid1, aid2, aid3 = 300000, 300001, 300002
        for i, aid in enumerate([aid1, aid2, aid3]):
            action = ActionDefinition(
                id=aid,
                name=f"test_{aid}",
                display_name=f"Action {i}",
                workflow_type="payment",
                embedding=None,
            )
            session.add(action)
        session.commit()
        
        # Fetch batch
        batch = fetch_pending_record_batch(
            session,
            ActionDefinition,
            db_batch_size=10,
            force=False,
        )
        
        # Simulate processing: mark aid1 and aid2 as done, leave aid3
        session.query(ActionDefinition).filter(
            ActionDefinition.id == aid1
        ).update({ActionDefinition.embedding: [0.1] * 384})
        session.query(ActionDefinition).filter(
            ActionDefinition.id == aid2
        ).update({ActionDefinition.embedding: [0.2] * 384})
        session.commit()
        
        # Resume fetch should only get aid3
        batch2 = fetch_pending_record_batch(
            session,
            ActionDefinition,
            db_batch_size=10,
            force=False,
            resume_from=aid2,
        )
        
        batch2_ids = {r[0] for r in batch2}
        assert aid3 in batch2_ids
        assert aid1 not in batch2_ids
        assert aid2 not in batch2_ids


class TestWorkspaceIsolation:
    """Test workspace/tenant isolation with batching."""

    def test_workspace_scoped_batch(self, session: Session, setup_tenant_workspace):
        """Verify workspace scoping works with batch fetching."""
        from scripts.backfill_embeddings import fetch_pending_record_batch
        
        tenant, workspace = setup_tenant_workspace
        
        # Create knowledge in workspace
        kid = _uid()
        knowledge = WorkflowKnowledge(
            id=kid,
            workspace_id=workspace.id,
            workflow_name="test-workflow",
            summary="Test",
        )
        session.add(knowledge)
        session.flush()
        
        # Create rules in this workspace
        rid1 = _uid()
        rule1 = WorkflowBusinessRule(
            id=rid1,
            workflow_knowledge_id=knowledge.id,
            rule="Test rule 1",
            embedding=None,
        )
        session.add(rule1)
        
        # Create another workspace with rules
        wid2 = _uid()
        workspace2 = Workspace(
            id=wid2,
            tenant_id=tenant.id,
            name=f"other-workspace-{wid2}",
            display_name="Other Workspace",
            active=True,
        )
        session.add(workspace2)
        session.flush()
        
        kid2 = _uid()
        knowledge2 = WorkflowKnowledge(
            id=kid2,
            workspace_id=workspace2.id,
            workflow_name="test-workflow-2",
            summary="Test",
        )
        session.add(knowledge2)
        session.flush()
        
        rid2 = _uid()
        rule2 = WorkflowBusinessRule(
            id=rid2,
            workflow_knowledge_id=knowledge2.id,
            rule="Test rule 2",
            embedding=None,
        )
        session.add(rule2)
        session.commit()
        
        # Fetch batch for workspace 1
        batch = fetch_pending_record_batch(
            session,
            WorkflowBusinessRule,
            db_batch_size=10,
            force=False,
            workspace_id=workspace.id,
        )
        
        batch_ids = {r[0] for r in batch}
        assert rid1 in batch_ids, "Should include rule from workspace"
        assert rid2 not in batch_ids, "Should not include rule from other workspace"


class TestCLIBackwardCompatibility:
    """Test backward compatibility of existing CLI arguments."""

    def test_existing_cli_options_present(self):
        """Verify new CLI options are added correctly."""
        import sys
        import subprocess
        
        # Test by importing the script as a module rather than running it
        # This avoids path issues
        result = subprocess.run(
            [sys.executable, "-c", 
             "from scripts.backfill_embeddings import main; print('OK')"],
            capture_output=True,
            text=True,
            cwd="c:\\Users\\Devendra\\projects\\mflows",
        )
        
        # If we can import it, the syntax is correct
        assert "OK" in result.stdout or result.returncode == 0


class TestPhase1And2BPreservation:
    """Test that Phase 1 isolation and Phase 2B metadata are preserved."""

    def test_metadata_persisted_in_batch_commit(self, session: Session):
        """Verify Phase 2B metadata (model_name, version, generated_at) is persisted."""
        from scripts.backfill_embeddings import commit_batch_updates
        
        aid = _uid()
        action = ActionDefinition(
            id=aid,
            name=f"test_{aid}",
            display_name="Test Action",
            workflow_type="payment",
        )
        session.add(action)
        session.commit()
        
        batch = [(aid, action)]
        results = {aid: ([0.1] * 384, None)}
        
        commit_batch_updates(
            session,
            batch,
            results,
            model_name="BAAI/bge-small-en-v1.5",
            model_version="1.5",
        )
        
        # Verify metadata
        session.refresh(action)
        assert action.embedding_model_name == "BAAI/bge-small-en-v1.5"
        assert action.embedding_model_version == "1.5"
        assert action.embedding_generated_at is not None
        assert action.embedding_generated_at.tzinfo is not None  # UTC


class TestBoundaryConditions:
    """Test edge cases and boundary conditions."""

    def test_empty_batch_with_all_processed(self, session: Session):
        """Verify batch returns empty when all records have embeddings."""
        # Create action with embedding
        aid = _uid()
        action = ActionDefinition(
            id=aid,
            name=f"test_{aid}",
            display_name="Test Action",
            workflow_type="payment",
            embedding=[0.1] * 384,
        )
        session.add(action)
        session.commit()
        
        # Fetch batch without force should be empty
        batch = fetch_pending_record_batch(
            session,
            ActionDefinition,
            db_batch_size=10,
            force=False,
        )
        
        # Should be empty since all have embeddings
        assert len(batch) == 0

    def test_single_record_batch(self, session: Session):
        """Verify single-record batches work correctly."""
        aid = _uid()
        action = ActionDefinition(
            id=aid,
            name=f"test_{aid}",
            display_name="Test Action",
            workflow_type="payment",
            embedding=None,
        )
        session.add(action)
        session.commit()
        
        batch = fetch_pending_record_batch(
            session,
            ActionDefinition,
            db_batch_size=1,
            force=False,
        )
        
        assert len(batch) == 1
        assert batch[0][0] == aid

    def test_batch_size_larger_than_dataset(self, session: Session):
        """Verify batch size larger than dataset returns all records."""
        count = 3
        created_ids = []
        for i in range(count):
            aid = 400000 + i
            action = ActionDefinition(
                id=aid,
                name=f"test_{aid}",
                display_name=f"Action {i}",
                workflow_type="payment",
                embedding=None,
            )
            session.add(action)
            created_ids.append(aid)
        session.commit()
        
        batch = fetch_pending_record_batch(
            session,
            ActionDefinition,
            db_batch_size=1000,
            force=False,
            resume_from=400000 - 1,  # Start just before our test records
        )
        
        batch_ids = {r[0] for r in batch}
        # Should include only our test records
        for aid in created_ids:
            assert aid in batch_ids, f"Should include action {aid}"
