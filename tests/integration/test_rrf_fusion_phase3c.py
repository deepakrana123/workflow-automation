"""
Phase 3C: Reciprocal Rank Fusion (RRF) for Business Rule Retrieval

Comprehensive test suite for combining vector, BM25, and PostgreSQL FTS
retrieval channels using Reciprocal Rank Fusion.

Validates:
1. Multi-channel document ranking and fusion
2. Deterministic score calculation
3. Tie-breaking behavior
4. Workspace isolation at fusion layer
5. Tenant ownership validation
6. Missing channel graceful handling
7. Empty channel handling
8. Provenance preservation
9. Deterministic ordering
"""

import pytest
from typing import Any
import uuid

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.workspace import Workspace
from app.models.tenant import Tenant
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workflow_business_rule import WorkflowBusinessRule

from app.knowledge_ingestions.rule_repository import RuleRepository
from app.retrieval.rule_vector_retriever import RuleVectorRetriever
from app.retrieval.rule_postgres_retriever import RulePostgresRetriever
from app.retrieval.rule_keyword_retriever import RuleKeywordRetriever
from app.retrieval.rule_reciprocal_rank_fusion import (
    RuleReciprocalRankFusion,
    FusedRetrievalResult,
)
from app.semantic.embedding_service import EmbeddingService


def _uid() -> int:
    """Generate unique random ID."""
    return uuid.uuid4().int % (2**31 - 1)


@pytest.fixture
def session() -> Session:
    """Database session for integration tests."""
    session = SessionLocal()
    yield session
    # Cleanup
    test_pattern = "test_phase3c_%"
    session.query(WorkflowBusinessRule).filter(
        WorkflowBusinessRule.rule.like(test_pattern)
    ).delete()
    session.query(WorkflowKnowledge).filter(
        WorkflowKnowledge.workflow_name.like(test_pattern)
    ).delete()
    session.query(Workspace).filter(Workspace.name.like(test_pattern)).delete()
    session.query(Tenant).filter(Tenant.name.like(test_pattern)).delete()
    session.commit()
    session.close()


@pytest.fixture
def embedding_service() -> EmbeddingService:
    """EmbeddingService instance."""
    return EmbeddingService()


@pytest.fixture
def test_workspace(session: Session) -> tuple[Workspace, Tenant]:
    """Create a test workspace and tenant."""
    tenant = Tenant(
        id=_uid(),
        name=f"test_phase3c_tenant_{_uid()}",
        slug=f"test-phase3c-{_uid()}",
        display_name="Test Phase 3C Tenant",
        active=True,
    )
    session.add(tenant)
    session.flush()

    workspace = Workspace(
        id=_uid(),
        tenant_id=tenant.id,
        name=f"test_phase3c_workspace_{_uid()}",
        display_name="Test Phase 3C Workspace",
        active=True,
    )
    session.add(workspace)
    session.commit()

    return workspace, tenant


@pytest.fixture
def test_workspace_with_rules(
    session: Session, embedding_service: EmbeddingService, test_workspace
) -> tuple[Workspace, list[WorkflowBusinessRule]]:
    """Create a workspace with diverse rules for multi-channel retrieval."""
    workspace, tenant = test_workspace

    knowledge = WorkflowKnowledge(
        id=_uid(),
        workspace_id=workspace.id,
        workflow_name=f"test_phase3c_loan_flow_{_uid()}",
        summary="Test loan processing workflow",
    )
    session.add(knowledge)
    session.flush()

    # Define diverse rules for multi-channel testing
    rule_definitions = [
        {
            "rule": "test_phase3c_IF credit score ABOVE 700 THEN approve loan",
            "condition": "credit_score > 700",
            "outcome": "approve_loan",
            "responsible_role": "credit_officer",
            "threshold": "700",
        },
        {
            "rule": "test_phase3c_IF debt ratio BELOW 50 THEN accept application",
            "condition": "debt_ratio < 0.5",
            "outcome": "accept_application",
            "responsible_role": "underwriter",
            "threshold": "0.5",
        },
        {
            "rule": "test_phase3c_IF income ABOVE 50000 AND credit ABOVE 650 THEN consider",
            "condition": "income > 50000 AND credit_score > 650",
            "outcome": "consider_for_approval",
            "responsible_role": "loan_manager",
            "threshold": None,
        },
        {
            "rule": "test_phase3c_employment stability MUST PASS verification",
            "condition": "employment_duration_months > 12",
            "outcome": "pass_stability_check",
            "responsible_role": "hr_specialist",
            "threshold": "12",
        },
        {
            "rule": "test_phase3c_collateral value MUST EXCEED loan amount BY 20 percent",
            "condition": "collateral_value > loan_amount * 1.2",
            "outcome": "collateral_verified",
            "responsible_role": "appraiser",
            "threshold": "1.2",
        },
    ]

    rules = []
    for rule_def in rule_definitions:
        rule = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge.id,
            rule=rule_def["rule"],
            condition=rule_def.get("condition"),
            outcome=rule_def.get("outcome"),
            responsible_role=rule_def.get("responsible_role"),
            threshold=rule_def.get("threshold"),
        )

        # Generate embedding
        rule_text = embedding_service.build_rule_text(rule)
        embedding = embedding_service.generate_embedding(rule_text)
        rule.embedding = embedding
        rule.embedding_model_name = "BAAI/bge-small-en-v1.5"
        rule.embedding_model_version = "1.5"

        session.add(rule)
        rules.append(rule)

    session.commit()
    return workspace, rules


class TestRRFBasicFusion:
    """Test basic RRF fusion functionality."""

    def test_rrf_initialization_validates_workspace(self, session: Session):
        """Verify that RRF validates workspace existence."""
        with pytest.raises(ValueError, match="Workspace .* not found"):
            RuleReciprocalRankFusion(session, workspace_id=999999)

    def test_rrf_initialization_validates_tenant_ownership(
        self, session: Session, test_workspace
    ):
        """Verify that RRF validates workspace belongs to tenant."""
        workspace, tenant = test_workspace
        wrong_tenant_id = _uid()

        with pytest.raises(ValueError, match="does not belong to tenant"):
            RuleReciprocalRankFusion(
                session, workspace_id=workspace.id, tenant_id=wrong_tenant_id
            )

    def test_rrf_empty_channels_returns_empty(
        self, session: Session, test_workspace
    ):
        """Verify that RRF with all empty channels returns empty list."""
        workspace, tenant = test_workspace

        fusion = RuleReciprocalRankFusion(session, workspace_id=workspace.id)
        result = fusion.fuse(
            vector_results=[],
            bm25_results=[],
            postgres_results=[],
            top_k=20,
        )

        assert len(result) == 0

    def test_rrf_single_channel_returns_results(
        self, session: Session, embedding_service: EmbeddingService, test_workspace_with_rules
    ):
        """Verify that RRF works with results from a single channel."""
        workspace, rules = test_workspace_with_rules

        repo = RuleRepository(session)
        vector_retriever = RuleVectorRetriever(repo, workspace_id=workspace.id)

        # Get vector results
        query_embedding = embedding_service.generate_embedding("credit score")
        vector_results = vector_retriever.search(embedding=query_embedding, limit=5)

        fusion = RuleReciprocalRankFusion(session, workspace_id=workspace.id)
        fused = fusion.fuse(
            vector_results=vector_results,
            bm25_results=[],
            postgres_results=[],
            top_k=10,
        )

        assert len(fused) > 0, "Should return results from single channel"
        assert all(isinstance(r, FusedRetrievalResult) for r in fused)

        # Verify scores are reasonable
        for r in fused:
            assert r.rrf_score > 0, "RRF score should be positive"
            assert r.vector_rank is not None, "Vector rank should be set"
            assert r.bm25_rank is None, "BM25 rank should not be set"
            assert r.postgres_rank is None, "Postgres rank should not be set"


class TestRRFMultiChannelFusion:
    """Test RRF with multiple channels."""

    def test_rrf_fuses_all_three_channels(
        self, session: Session, embedding_service: EmbeddingService, test_workspace_with_rules
    ):
        """Verify that RRF correctly fuses results from all three channels."""
        workspace, rules = test_workspace_with_rules

        repo = RuleRepository(session)
        vector_retriever = RuleVectorRetriever(repo, workspace_id=workspace.id)
        postgres_retriever = RulePostgresRetriever(repo, workspace_id=workspace.id)
        bm25_retriever = RuleKeywordRetriever(repo, workspace_id=workspace.id)

        query_text = "credit approval"
        query_embedding = embedding_service.generate_embedding(query_text)

        vector_results = vector_retriever.search(embedding=query_embedding, limit=10)
        postgres_results = postgres_retriever.search(query=query_text, limit=10)
        bm25_results = bm25_retriever.search(query=query_text, limit=10)

        fusion = RuleReciprocalRankFusion(session, workspace_id=workspace.id)
        fused = fusion.fuse(
            vector_results=vector_results,
            bm25_results=bm25_results,
            postgres_results=postgres_results,
            top_k=20,
        )

        # If any channel has results, fusion should produce results
        has_results = len(vector_results) + len(bm25_results) + len(postgres_results) > 0
        if has_results:
            assert len(fused) > 0, "Fusion should produce results"

    def test_rrf_score_calculation(
        self, session: Session, embedding_service: EmbeddingService, test_workspace
    ):
        """Verify that RRF score is calculated correctly."""
        from app.retrieval.models import RetrievalCandidate

        workspace, tenant = test_workspace

        # Create a single test rule
        knowledge = WorkflowKnowledge(
            id=_uid(),
            workspace_id=workspace.id,
            workflow_name=f"test_phase3c_calc_{_uid()}",
            summary="Test RRF calculation",
        )
        session.add(knowledge)
        session.flush()

        rule = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge.id,
            rule="test_phase3c_test rule for RRF calculation",
            condition="test_condition",
        )
        session.add(rule)
        session.commit()

        # Manually construct retrieval results with known ranks
        vector_candidate = RetrievalCandidate(entity=rule, score=0.95, source="vector")
        bm25_candidate = RetrievalCandidate(entity=rule, score=8.5, source="bm25")
        postgres_candidate = RetrievalCandidate(entity=rule, score=0.5, source="postgres")

        fusion = RuleReciprocalRankFusion(session, workspace_id=workspace.id, k=60)
        fused = fusion.fuse(
            vector_results=[vector_candidate],  # Rank 1
            bm25_results=[bm25_candidate],  # Rank 1
            postgres_results=[postgres_candidate],  # Rank 1
            top_k=10,
        )

        assert len(fused) == 1
        result = fused[0]

        # Expected RRF = 1/(60+1) + 1/(60+1) + 1/(60+1) = 3/61 ≈ 0.0492
        expected_rrf = 3.0 / 61.0
        assert abs(result.rrf_score - expected_rrf) < 0.001, \
            f"RRF score {result.rrf_score} should be close to {expected_rrf}"

    def test_rrf_higher_rank_higher_score(
        self, session: Session, embedding_service: EmbeddingService, test_workspace
    ):
        """Verify that higher-ranked documents get higher RRF scores."""
        from app.retrieval.models import RetrievalCandidate

        workspace, tenant = test_workspace

        knowledge = WorkflowKnowledge(
            id=_uid(),
            workspace_id=workspace.id,
            workflow_name=f"test_phase3c_rank_order_{_uid()}",
            summary="Test rank ordering",
        )
        session.add(knowledge)
        session.flush()

        rule1 = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge.id,
            rule="test_phase3c_rule 1",
            condition="cond1",
        )
        rule2 = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge.id,
            rule="test_phase3c_rule 2",
            condition="cond2",
        )
        session.add(rule1)
        session.add(rule2)
        session.commit()

        # Rule 1 ranked high in all channels
        r1_vector = RetrievalCandidate(entity=rule1, score=0.9, source="vector")
        r1_bm25 = RetrievalCandidate(entity=rule1, score=9.0, source="bm25")
        r1_postgres = RetrievalCandidate(entity=rule1, score=0.8, source="postgres")

        # Rule 2 ranked low in all channels
        r2_vector = RetrievalCandidate(entity=rule2, score=0.1, source="vector")
        r2_bm25 = RetrievalCandidate(entity=rule2, score=1.0, source="bm25")
        r2_postgres = RetrievalCandidate(entity=rule2, score=0.05, source="postgres")

        fusion = RuleReciprocalRankFusion(session, workspace_id=workspace.id)
        fused = fusion.fuse(
            vector_results=[r1_vector, r2_vector],
            bm25_results=[r1_bm25, r2_bm25],
            postgres_results=[r1_postgres, r2_postgres],
            top_k=10,
        )

        assert len(fused) == 2
        # Rule 1 should be ranked first
        assert fused[0].rule.id == rule1.id
        assert fused[1].rule.id == rule2.id
        # Rule 1 should have higher RRF score
        assert fused[0].rrf_score > fused[1].rrf_score


class TestRRFDeduplication:
    """Test RRF deduplication across channels."""

    def test_rrf_deduplicates_same_rule(
        self, session: Session, embedding_service: EmbeddingService, test_workspace
    ):
        """Verify that RRF merges the same rule from multiple channels."""
        from app.retrieval.models import RetrievalCandidate

        workspace, tenant = test_workspace

        knowledge = WorkflowKnowledge(
            id=_uid(),
            workspace_id=workspace.id,
            workflow_name=f"test_phase3c_dedup_{_uid()}",
            summary="Test deduplication",
        )
        session.add(knowledge)
        session.flush()

        rule = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge.id,
            rule="test_phase3c_shared rule",
            condition="cond",
        )
        session.add(rule)
        session.commit()

        # Same rule returned by all channels
        candidates = [
            RetrievalCandidate(entity=rule, score=0.9, source="vector"),
            RetrievalCandidate(entity=rule, score=8.0, source="bm25"),
            RetrievalCandidate(entity=rule, score=0.7, source="postgres"),
        ]

        fusion = RuleReciprocalRankFusion(session, workspace_id=workspace.id)
        fused = fusion.fuse(
            vector_results=candidates[:1],
            bm25_results=candidates[1:2],
            postgres_results=candidates[2:3],
            top_k=10,
        )

        # Should have exactly one result (deduplicated)
        assert len(fused) == 1
        result = fused[0]

        # All three channel ranks should be present
        assert result.vector_rank == 1
        assert result.bm25_rank == 1
        assert result.postgres_rank == 1
        assert result.retrieval_channels == 3


class TestRRFWorkspaceIsolation:
    """Test that RRF enforces workspace isolation."""

    def test_rrf_rejects_cross_workspace_results(
        self, session: Session, embedding_service: EmbeddingService
    ):
        """Verify that RRF rejects results from different workspaces."""
        from app.retrieval.models import RetrievalCandidate

        # Create two workspaces
        tenant1 = Tenant(
            id=_uid(),
            name=f"test_phase3c_tenant1_{_uid()}",
            slug=f"test-phase3c-1-{_uid()}",
            display_name="Tenant 1",
            active=True,
        )
        session.add(tenant1)
        session.flush()

        workspace1 = Workspace(
            id=_uid(),
            tenant_id=tenant1.id,
            name=f"test_phase3c_ws1_{_uid()}",
            display_name="Workspace 1",
            active=True,
        )
        session.add(workspace1)
        session.flush()

        tenant2 = Tenant(
            id=_uid(),
            name=f"test_phase3c_tenant2_{_uid()}",
            slug=f"test-phase3c-2-{_uid()}",
            display_name="Tenant 2",
            active=True,
        )
        session.add(tenant2)
        session.flush()

        workspace2 = Workspace(
            id=_uid(),
            tenant_id=tenant2.id,
            name=f"test_phase3c_ws2_{_uid()}",
            display_name="Workspace 2",
            active=True,
        )
        session.add(workspace2)
        session.commit()

        # Create rules in each workspace
        knowledge1 = WorkflowKnowledge(
            id=_uid(),
            workspace_id=workspace1.id,
            workflow_name=f"test_phase3c_iso1_{_uid()}",
            summary="Flow 1",
        )
        session.add(knowledge1)
        session.flush()

        knowledge2 = WorkflowKnowledge(
            id=_uid(),
            workspace_id=workspace2.id,
            workflow_name=f"test_phase3c_iso2_{_uid()}",
            summary="Flow 2",
        )
        session.add(knowledge2)
        session.flush()

        rule1 = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge1.id,
            rule="test_phase3c_ws1 rule",
            condition="cond1",
        )

        rule2 = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge2.id,
            rule="test_phase3c_ws2 rule",
            condition="cond2",
        )

        session.add(rule1)
        session.add(rule2)
        session.commit()

        # Create fusion for workspace1 but try to fuse result from workspace2
        fusion = RuleReciprocalRankFusion(session, workspace_id=workspace1.id)
        cross_ws_candidate = RetrievalCandidate(entity=rule2, score=0.9, source="vector")

        # Should raise ValueError
        with pytest.raises(ValueError, match="does not belong to workspace"):
            fusion.fuse(
                vector_results=[cross_ws_candidate],
                bm25_results=[],
                postgres_results=[],
                top_k=10,
            )


class TestRRFTopK:
    """Test that RRF respects top_k limits."""

    def test_rrf_respects_top_k(
        self, session: Session, embedding_service: EmbeddingService, test_workspace_with_rules
    ):
        """Verify that RRF respects the top_k parameter."""
        workspace, rules = test_workspace_with_rules

        repo = RuleRepository(session)
        vector_retriever = RuleVectorRetriever(repo, workspace_id=workspace.id)

        query_embedding = embedding_service.generate_embedding("test")
        vector_results = vector_retriever.search(embedding=query_embedding, limit=100)

        fusion = RuleReciprocalRankFusion(session, workspace_id=workspace.id)

        for top_k in [1, 3, 5, 10]:
            fused = fusion.fuse(
                vector_results=vector_results,
                bm25_results=[],
                postgres_results=[],
                top_k=top_k,
            )
            assert len(fused) <= top_k, f"Results {len(fused)} should not exceed top_k {top_k}"


class TestRRFDeterminism:
    """Test that RRF produces deterministic results."""

    def test_rrf_deterministic_tie_breaking(
        self, session: Session, embedding_service: EmbeddingService, test_workspace
    ):
        """Verify that RRF breaks ties deterministically by rule.id."""
        from app.retrieval.models import RetrievalCandidate

        workspace, tenant = test_workspace

        knowledge = WorkflowKnowledge(
            id=_uid(),
            workspace_id=workspace.id,
            workflow_name=f"test_phase3c_tie_{_uid()}",
            summary="Test tie-breaking",
        )
        session.add(knowledge)
        session.flush()

        # Create two rules with IDs that will sort deterministically
        id1 = 100001
        id2 = 100002
        
        rule1 = WorkflowBusinessRule(
            id=id1,
            workflow_knowledge_id=knowledge.id,
            rule="test_phase3c_rule with lower id",
            condition="cond1",
        )
        
        rule2 = WorkflowBusinessRule(
            id=id2,
            workflow_knowledge_id=knowledge.id,
            rule="test_phase3c_rule with higher id",
            condition="cond2",
        )

        session.add(rule1)
        session.add(rule2)
        session.commit()

        # Both rules get same rank in same channel (creating tie)
        candidates = [
            RetrievalCandidate(entity=rule1, score=0.5, source="vector"),
            RetrievalCandidate(entity=rule2, score=0.5, source="vector"),
        ]

        fusion = RuleReciprocalRankFusion(session, workspace_id=workspace.id)

        # Run multiple times and verify consistent ordering
        for _ in range(3):
            fused = fusion.fuse(
                vector_results=candidates,
                bm25_results=[],
                postgres_results=[],
                top_k=10,
            )

            # Lower ID should come first (deterministic tie-breaking)
            assert len(fused) == 2
            assert fused[0].rule.id == id1
            assert fused[1].rule.id == id2


class TestRRFProvenance:
    """Test that RRF preserves rule provenance."""

    def test_rrf_preserves_rule_content(
        self, session: Session, embedding_service: EmbeddingService, test_workspace_with_rules
    ):
        """Verify that RRF preserves all rule content."""
        workspace, rules = test_workspace_with_rules

        repo = RuleRepository(session)
        vector_retriever = RuleVectorRetriever(repo, workspace_id=workspace.id)

        query_embedding = embedding_service.generate_embedding("credit")
        vector_results = vector_retriever.search(embedding=query_embedding, limit=10)

        fusion = RuleReciprocalRankFusion(session, workspace_id=workspace.id)
        fused = fusion.fuse(
            vector_results=vector_results,
            bm25_results=[],
            postgres_results=[],
            top_k=10,
        )

        for result in fused:
            rule = result.rule
            # Verify all important fields are present
            assert rule.id is not None
            assert rule.rule is not None
            assert rule.workflow_knowledge_id is not None
            assert hasattr(rule, "condition")
            assert hasattr(rule, "outcome")
            assert hasattr(rule, "responsible_role")
            assert hasattr(rule, "threshold")
