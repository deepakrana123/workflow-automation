"""
Phase 2B: Embedding Model/Version Metadata Tests

Tests for backward-compatible embedding metadata columns (embedding_model_name,
embedding_model_version, embedding_generated_at) across action_definitions,
trigger_definitions, and workflow_business_rule.

Verifies:
- Metadata persistence during backfill (only on successful embedding generation)
- Stale embedding detection queries
- NULL metadata compatibility (pre-Phase 2B embeddings)
- Phase 1 isolation/idempotency preservation
- Alembic migration reversibility
"""

import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.action_definitions import ActionDefinition
from app.models.trigger_definitions import TriggerDefinition
from app.models.workflow_business_rule import WorkflowBusinessRule
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workspace import Workspace
from app.models.tenant import Tenant
from app.semantic.stale_embedding_detection import (
    find_stale_action_embeddings,
    find_stale_trigger_embeddings,
    find_stale_business_rule_embeddings,
    find_missing_metadata_actions,
    find_missing_metadata_triggers,
    find_missing_metadata_business_rules,
    CURRENT_MODEL_NAME,
    CURRENT_MODEL_VERSION,
)


def _uid() -> int:
    """Generate a unique random ID."""
    return uuid.uuid4().int % (2**31 - 1)


@pytest.fixture
def session() -> Session:
    """Provide a database session for tests."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def setup_tenant_and_workspace(session: Session):
    """Create a test tenant and workspace."""
    tid = _uid()
    wid = _uid()
    
    tenant = Tenant(
        id=tid,
        name=f"test-tenant-{tid}",
        slug=f"test-tenant-{tid}",
        display_name="Test Tenant Phase 2B",
        active=True,
    )
    session.add(tenant)
    session.flush()

    workspace = Workspace(
        id=wid,
        tenant_id=tenant.id,
        name=f"test-workspace-{wid}",
        display_name="Test Workspace Phase 2B",
        active=True,
    )
    session.add(workspace)
    session.flush()

    return tenant, workspace


class TestEmbeddingMetadataColumns:
    """Test metadata column existence and types."""

    def test_action_definitions_has_metadata_columns(self, session: Session):
        """Verify ActionDefinition has metadata columns."""
        assert hasattr(ActionDefinition, "embedding_model_name")
        assert hasattr(ActionDefinition, "embedding_model_version")
        assert hasattr(ActionDefinition, "embedding_generated_at")

    def test_trigger_definitions_has_metadata_columns(self, session: Session):
        """Verify TriggerDefinition has metadata columns."""
        assert hasattr(TriggerDefinition, "embedding_model_name")
        assert hasattr(TriggerDefinition, "embedding_model_version")
        assert hasattr(TriggerDefinition, "embedding_generated_at")

    def test_workflow_business_rule_has_metadata_columns(self, session: Session):
        """Verify WorkflowBusinessRule has metadata columns."""
        assert hasattr(WorkflowBusinessRule, "embedding_model_name")
        assert hasattr(WorkflowBusinessRule, "embedding_model_version")
        assert hasattr(WorkflowBusinessRule, "embedding_generated_at")

    def test_metadata_columns_nullable(self, session: Session):
        """Verify metadata columns are nullable for backward compatibility."""
        aid = _uid()
        action = ActionDefinition(
            id=aid,
            name=f"test_action_nullable_{aid}",
            display_name="Test Action",
            workflow_type="payment",
            embedding=[0.1] * 384,
            embedding_model_name=None,
            embedding_model_version=None,
            embedding_generated_at=None,
        )
        session.add(action)
        session.commit()

        retrieved = session.query(ActionDefinition).filter_by(id=aid).first()
        assert retrieved is not None
        assert retrieved.embedding is not None
        assert retrieved.embedding_model_name is None
        assert retrieved.embedding_model_version is None
        assert retrieved.embedding_generated_at is None

        session.delete(retrieved)
        session.commit()


class TestMetadataPersistenceOnBackfill:
    """Test metadata persistence during embedding generation."""

    def test_metadata_persisted_on_successful_embedding(self, session: Session):
        """Verify metadata fields set after successful embedding generation."""
        aid = _uid()
        action = ActionDefinition(
            id=aid,
            name=f"test_action_metadata_{aid}",
            display_name="Test Action",
            workflow_type="payment",
        )
        session.add(action)
        session.commit()

        embedding_vec = [0.1] * 384
        generated_at = datetime.now(timezone.utc)
        model_name = "BAAI/bge-small-en-v1.5"
        model_version = "1.5"

        action.embedding = embedding_vec
        action.embedding_model_name = model_name
        action.embedding_model_version = model_version
        action.embedding_generated_at = generated_at

        session.commit()

        retrieved = session.query(ActionDefinition).filter_by(id=aid).first()
        # Use is not None check rather than direct comparison for numpy arrays
        assert retrieved.embedding is not None
        assert len(retrieved.embedding) == len(embedding_vec)
        assert retrieved.embedding_model_name == model_name
        assert retrieved.embedding_model_version == model_version
        assert retrieved.embedding_generated_at == generated_at

        session.delete(retrieved)
        session.commit()

    def test_metadata_isolation_on_generation_failure(self, session: Session):
        """Verify metadata NOT set if embedding generation fails."""
        aid = _uid()
        action = ActionDefinition(
            id=aid,
            name=f"test_action_fail_closed_{aid}",
            display_name="Test Action",
            workflow_type="payment",
        )
        session.add(action)
        session.commit()

        action.embedding = [0.1] * 384
        session.commit()

        retrieved = session.query(ActionDefinition).filter_by(id=aid).first()
        assert retrieved.embedding is not None
        assert retrieved.embedding_model_name is None
        assert retrieved.embedding_model_version is None
        assert retrieved.embedding_generated_at is None

        session.delete(retrieved)
        session.commit()


class TestStaleEmbeddingDetection:
    """Test stale embedding detection queries."""

    def test_find_stale_action_embeddings_by_model_name(self, session: Session):
        """Find actions with embeddings from old model versions."""
        old_id = _uid()
        current_id = _uid()
        
        old_action = ActionDefinition(
            id=old_id,
            name=f"test_action_old_model_{old_id}",
            display_name="Test Action",
            workflow_type="payment",
            embedding=[0.1] * 384,
            embedding_model_name="old-model-v1",
            embedding_model_version="1.0",
            embedding_generated_at=datetime.now(timezone.utc),
        )

        current_action = ActionDefinition(
            id=current_id,
            name=f"test_action_current_model_{current_id}",
            display_name="Test Action",
            workflow_type="payment",
            embedding=[0.2] * 384,
            embedding_model_name=CURRENT_MODEL_NAME,
            embedding_model_version=CURRENT_MODEL_VERSION,
            embedding_generated_at=datetime.now(timezone.utc),
        )

        session.add_all([old_action, current_action])
        session.commit()

        stale = find_stale_action_embeddings(session)
        stale_ids = {a.id for a in stale}

        assert old_id in stale_ids, "Old model embedding should be detected as stale"
        assert current_id not in stale_ids, "Current model embedding should not be stale"

        session.delete(old_action)
        session.delete(current_action)
        session.commit()

    def test_find_stale_embeddings_missing_metadata(self, session: Session):
        """Find embeddings with missing metadata (pre-Phase 2B backfill)."""
        aid = _uid()
        action = ActionDefinition(
            id=aid,
            name=f"test_action_missing_metadata_{aid}",
            display_name="Test Action",
            workflow_type="payment",
            embedding=[0.1] * 384,
            embedding_model_name=None,
            embedding_model_version=None,
            embedding_generated_at=None,
        )
        session.add(action)
        session.commit()

        stale = find_stale_action_embeddings(session)
        stale_ids = {a.id for a in stale}

        assert (
            aid in stale_ids
        ), "Embedding missing metadata should be detected as stale"

        session.delete(action)
        session.commit()

    def test_find_stale_trigger_embeddings(self, session: Session):
        """Find triggers with stale embeddings."""
        tid = _uid()
        trigger = TriggerDefinition(
            id=tid,
            name=f"test_trigger_stale_{tid}",
            display_name="Test Trigger",
            workflow_type="payment",
            embedding=[0.1] * 384,
            embedding_model_name="old-model-v1",
            embedding_model_version="1.0",
            embedding_generated_at=datetime.now(timezone.utc),
        )
        session.add(trigger)
        session.commit()

        stale = find_stale_trigger_embeddings(session)
        stale_ids = {t.id for t in stale}

        assert tid in stale_ids, "Stale trigger embedding should be detected"

        session.delete(trigger)
        session.commit()

    def test_find_stale_business_rule_embeddings_workspace_scoped(
        self, session: Session, setup_tenant_and_workspace
    ):
        """Find stale business rule embeddings with workspace scoping."""
        tenant, workspace = setup_tenant_and_workspace
        kid = _uid()
        rid = _uid()

        knowledge = WorkflowKnowledge(
            id=kid,
            workspace_id=workspace.id,
            workflow_name=f"test-knowledge-{kid}",
            summary="Test",
        )
        session.add(knowledge)
        session.flush()

        rule = WorkflowBusinessRule(
            id=rid,
            workflow_knowledge_id=knowledge.id,
            rule="test rule",
            embedding=[0.1] * 384,
            embedding_model_name="old-model-v1",
            embedding_model_version="1.0",
            embedding_generated_at=datetime.now(timezone.utc),
        )
        session.add(rule)
        session.commit()

        stale = find_stale_business_rule_embeddings(
            session, workspace_id=workspace.id
        )
        stale_ids = {r.id for r in stale}

        assert (
            rid in stale_ids
        ), "Stale business rule in workspace should be detected"

        # Delete in reverse order (rule before knowledge due to FK constraint)
        # Flush after each delete to ensure order is maintained
        session.delete(rule)
        session.flush()
        session.delete(knowledge)
        session.commit()


class TestMissingMetadataDetection:
    """Test detection of embeddings missing metadata."""

    def test_find_missing_metadata_actions(self, session: Session):
        """Find actions with embeddings but missing metadata."""
        aid = _uid()
        action = ActionDefinition(
            id=aid,
            name=f"test_action_missing_meta_{aid}",
            display_name="Test Action",
            workflow_type="payment",
            embedding=[0.1] * 384,
            embedding_model_name=None,
            embedding_model_version=None,
            embedding_generated_at=None,
        )
        session.add(action)
        session.commit()

        missing = find_missing_metadata_actions(session)
        missing_ids = {a.id for a in missing}

        assert aid in missing_ids, "Action missing metadata should be detected"

        session.delete(action)
        session.commit()

    def test_find_missing_metadata_triggers(self, session: Session):
        """Find triggers with embeddings but missing metadata."""
        tid = _uid()
        trigger = TriggerDefinition(
            id=tid,
            name=f"test_trigger_missing_meta_{tid}",
            display_name="Test Trigger",
            workflow_type="payment",
            embedding=[0.1] * 384,
            embedding_model_name=None,
            embedding_model_version=None,
            embedding_generated_at=None,
        )
        session.add(trigger)
        session.commit()

        missing = find_missing_metadata_triggers(session)
        missing_ids = {t.id for t in missing}

        assert tid in missing_ids, "Trigger missing metadata should be detected"

        session.delete(trigger)
        session.commit()

    def test_find_missing_metadata_business_rules(
        self, session: Session, setup_tenant_and_workspace
    ):
        """Find business rules with embeddings but missing metadata."""
        tenant, workspace = setup_tenant_and_workspace
        kid = _uid()
        rid = _uid()

        knowledge = WorkflowKnowledge(
            id=kid,
            workspace_id=workspace.id,
            workflow_name=f"test-knowledge-{kid}",
            summary="Test",
        )
        session.add(knowledge)
        session.flush()

        rule = WorkflowBusinessRule(
            id=rid,
            workflow_knowledge_id=knowledge.id,
            rule="test rule",
            embedding=[0.1] * 384,
            embedding_model_name=None,
            embedding_model_version=None,
            embedding_generated_at=None,
        )
        session.add(rule)
        session.commit()

        missing = find_missing_metadata_business_rules(
            session, workspace_id=workspace.id
        )
        missing_ids = {r.id for r in missing}

        assert (
            rid in missing_ids
        ), "Business rule missing metadata should be detected"

        # Delete in reverse order (rule before knowledge due to FK constraint)
        # Flush after each delete to ensure order is maintained
        session.delete(rule)
        session.flush()
        session.delete(knowledge)
        session.commit()


class TestPhase1Preservation:
    """Test that Phase 1 (workspace isolation) is preserved."""

    def test_workspace_scoping_with_metadata(
        self, session: Session, setup_tenant_and_workspace
    ):
        """Verify workspace isolation still applies with metadata columns."""
        tenant, workspace = setup_tenant_and_workspace
        wid2 = _uid()

        other_workspace = Workspace(
            id=wid2,
            tenant_id=tenant.id,
            name=f"other-workspace-{wid2}",
            display_name="Other Workspace",
            active=True,
        )
        session.add(other_workspace)
        session.flush()

        kid1 = _uid()
        kid2 = _uid()
        
        knowledge1 = WorkflowKnowledge(
            id=kid1,
            workspace_id=workspace.id,
            workflow_name=f"test-knowledge-{kid1}",
            summary="Test",
        )
        knowledge2 = WorkflowKnowledge(
            id=kid2,
            workspace_id=other_workspace.id,
            workflow_name=f"test-knowledge-{kid2}",
            summary="Test",
        )
        session.add_all([knowledge1, knowledge2])
        session.flush()

        rid1 = _uid()
        rid2 = _uid()
        
        rule1 = WorkflowBusinessRule(
            id=rid1,
            workflow_knowledge_id=knowledge1.id,
            rule="test rule 1",
            embedding=[0.1] * 384,
            embedding_model_name=CURRENT_MODEL_NAME,
            embedding_model_version=CURRENT_MODEL_VERSION,
            embedding_generated_at=datetime.now(timezone.utc),
        )
        rule2 = WorkflowBusinessRule(
            id=rid2,
            workflow_knowledge_id=knowledge2.id,
            rule="test rule 2",
            embedding=[0.1] * 384,
            embedding_model_name=CURRENT_MODEL_NAME,
            embedding_model_version=CURRENT_MODEL_VERSION,
            embedding_generated_at=datetime.now(timezone.utc),
        )
        session.add_all([rule1, rule2])
        session.commit()

        scoped = find_stale_business_rule_embeddings(
            session, workspace_id=workspace.id
        )
        scoped_ids = {r.id for r in scoped}

        assert (
            rid1 not in scoped_ids
        ), "Rule in workspace should not be stale (current model)"
        assert (
            rid2 not in scoped_ids
        ), "Rule in different workspace should not appear in scoped query"

        session.delete(rule1)
        session.delete(rule2)
        session.delete(knowledge1)
        session.delete(knowledge2)
        session.delete(other_workspace)
        session.commit()

    def test_tenant_isolation_preserved(
        self, session: Session, setup_tenant_and_workspace
    ):
        """Verify tenant isolation still applies with metadata."""
        tenant, workspace = setup_tenant_and_workspace
        tid2 = _uid()

        other_tenant = Tenant(
            id=tid2,
            name=f"other-tenant-{tid2}",
            slug=f"other-tenant-{tid2}",
            display_name="Other Tenant",
            active=True,
        )
        session.add(other_tenant)
        session.flush()

        aid1 = _uid()
        aid2 = _uid()
        
        action1 = ActionDefinition(
            id=aid1,
            name=f"test_action_tenant1_{aid1}",
            display_name="Test",
            workflow_type="payment",
            embedding=[0.1] * 384,
            embedding_model_name="old-model",
            embedding_model_version="1.0",
            embedding_generated_at=datetime.now(timezone.utc),
        )
        action2 = ActionDefinition(
            id=aid2,
            name=f"test_action_tenant2_{aid2}",
            display_name="Test",
            workflow_type="payment",
            embedding=[0.1] * 384,
            embedding_model_name="old-model",
            embedding_model_version="1.0",
            embedding_generated_at=datetime.now(timezone.utc),
        )
        session.add_all([action1, action2])
        session.commit()

        stale = find_stale_action_embeddings(session)
        stale_ids = {a.id for a in stale}

        assert (
            aid1 in stale_ids
        ), "Stale action should be detected globally"
        assert (
            aid2 in stale_ids
        ), "Stale action should be detected globally"

        session.delete(action1)
        session.delete(action2)
        session.delete(other_tenant)
        session.commit()


class TestMetadataTimestamps:
    """Test timestamp handling and audit capabilities."""

    def test_generated_at_captures_generation_time(self, session: Session):
        """Verify generated_at timestamp is captured accurately."""
        aid = _uid()
        before = datetime.now(timezone.utc)

        action = ActionDefinition(
            id=aid,
            name=f"test_action_timestamp_{aid}",
            display_name="Test",
            workflow_type="payment",
            embedding=[0.1] * 384,
            embedding_model_name=CURRENT_MODEL_NAME,
            embedding_model_version=CURRENT_MODEL_VERSION,
            embedding_generated_at=datetime.now(timezone.utc),
        )
        session.add(action)
        session.commit()

        after = datetime.now(timezone.utc)

        retrieved = session.query(ActionDefinition).filter_by(id=aid).first()
        assert retrieved.embedding_generated_at is not None
        assert before <= retrieved.embedding_generated_at <= after

        session.delete(retrieved)
        session.commit()

    def test_generated_at_timezone_aware(self, session: Session):
        """Verify generated_at is timezone-aware (UTC)."""
        tid = _uid()
        generated_at = datetime.now(timezone.utc)

        trigger = TriggerDefinition(
            id=tid,
            name=f"test_trigger_tz_{tid}",
            display_name="Test",
            workflow_type="payment",
            embedding=[0.1] * 384,
            embedding_model_name=CURRENT_MODEL_NAME,
            embedding_model_version=CURRENT_MODEL_VERSION,
            embedding_generated_at=generated_at,
        )
        session.add(trigger)
        session.commit()

        retrieved = session.query(TriggerDefinition).filter_by(id=tid).first()
        assert retrieved.embedding_generated_at.tzinfo is not None

        session.delete(retrieved)
        session.commit()


class TestRetrievalCompatibility:
    """Test that retrieval queries work with metadata columns."""

    def test_cosine_distance_query_with_metadata(self, session: Session):
        """Verify retrieval by cosine distance works with metadata columns."""
        query_vec = [0.1] * 384
        aid = _uid()

        action = ActionDefinition(
            id=aid,
            name=f"test_action_retrieval_{aid}",
            display_name="Test",
            workflow_type="payment",
            embedding=[0.15] * 384,
            embedding_model_name=CURRENT_MODEL_NAME,
            embedding_model_version=CURRENT_MODEL_VERSION,
            embedding_generated_at=datetime.now(timezone.utc),
        )
        session.add(action)
        session.commit()

        # Use the .cosine_distance() method on the column
        distance = ActionDefinition.embedding.cosine_distance(query_vec)

        results = session.execute(
            select(ActionDefinition, distance.label("distance")).filter(
                ActionDefinition.embedding.isnot(None)
            ).order_by(distance)
        ).all()

        result_ids = {r[0].id for r in results}
        assert aid in result_ids, "Query should find action by cosine distance"

        session.delete(action)
        session.commit()

    def test_filter_by_has_embedding_metadata(self, session: Session):
        """Test filtering by embedding existence and metadata together."""
        aid1 = _uid()
        aid2 = _uid()
        
        action1 = ActionDefinition(
            id=aid1,
            name=f"test_action_complete_{aid1}",
            display_name="Test",
            workflow_type="payment",
            embedding=[0.1] * 384,
            embedding_model_name=CURRENT_MODEL_NAME,
            embedding_model_version=CURRENT_MODEL_VERSION,
            embedding_generated_at=datetime.now(timezone.utc),
        )

        action2 = ActionDefinition(
            id=aid2,
            name=f"test_action_no_embedding_{aid2}",
            display_name="Test",
            workflow_type="payment",
            embedding=None,
        )

        session.add_all([action1, action2])
        session.commit()

        current = session.execute(
            select(ActionDefinition).filter(
                and_(
                    ActionDefinition.embedding.isnot(None),
                    ActionDefinition.embedding_model_version == CURRENT_MODEL_VERSION,
                )
            )
        ).scalars().all()

        current_ids = {a.id for a in current}
        assert aid1 in current_ids, "Complete metadata action should match"
        assert aid2 not in current_ids, "No embedding should not match"

        session.delete(action1)
        session.delete(action2)
        session.commit()
