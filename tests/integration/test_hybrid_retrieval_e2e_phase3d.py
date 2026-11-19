"""
Phase 3D: End-to-End Hybrid Retrieval Validation

Comprehensive integration test suite for the complete Business Rule hybrid retrieval pipeline:
Vector Retrieval → BM25 Keyword Retrieval → PostgreSQL FTS Retrieval → RRF Fusion

This tests the actual end-to-end flow against a real database with synthetic banking rules.

Validates:
1. Complete retrieval pipeline functionality
2. Tenant and workspace isolation at response boundary
3. Result deduplication and ranking
4. Failure handling and edge cases
5. Deterministic output ordering
6. Provenance preservation
"""

import pytest
import time
from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.workspace import Workspace
from app.models.tenant import Tenant
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workflow_business_rule import WorkflowBusinessRule

from app.knowledge_ingestions.rule_repository import RuleRepository
from app.retrieval.rule_vector_retriever import RuleVectorRetriever
from app.retrieval.rule_keyword_retriever import RuleKeywordRetriever
from app.retrieval.rule_postgres_retriever import RulePostgresRetriever
from app.retrieval.rule_reciprocal_rank_fusion import RuleReciprocalRankFusion
from app.semantic.embedding_service import EmbeddingService


def _uid() -> int:
    """Generate unique random ID."""
    return uuid.uuid4().int % (2**31 - 1)


@pytest.fixture
def session() -> Session:
    """Database session for integration tests."""
    session = SessionLocal()
    yield session
    # Cleanup: delete all test-owned records
    test_pattern = "test_phase3d_%"
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
def alpha_and_beta_workspaces(session: Session) -> dict:
    """Create two isolated tenants with personal loan workspaces."""
    # Tenant Alpha
    alpha_tenant = Tenant(
        id=_uid(),
        name=f"test_phase3d_alpha_{_uid()}",
        slug=f"test-phase3d-alpha-{_uid()}",
        display_name="Alpha Bank",
        active=True,
    )
    session.add(alpha_tenant)
    session.flush()

    alpha_workspace = Workspace(
        id=_uid(),
        tenant_id=alpha_tenant.id,
        name=f"test_phase3d_alpha_personal_loan_{_uid()}",
        display_name="Alpha Personal Loan",
        active=True,
    )
    session.add(alpha_workspace)
    session.flush()

    # Tenant Beta
    beta_tenant = Tenant(
        id=_uid(),
        name=f"test_phase3d_beta_{_uid()}",
        slug=f"test-phase3d-beta-{_uid()}",
        display_name="Beta Bank",
        active=True,
    )
    session.add(beta_tenant)
    session.flush()

    beta_workspace = Workspace(
        id=_uid(),
        tenant_id=beta_tenant.id,
        name=f"test_phase3d_beta_personal_loan_{_uid()}",
        display_name="Beta Personal Loan",
        active=True,
    )
    session.add(beta_workspace)
    session.commit()

    return {
        "alpha": {
            "tenant": alpha_tenant,
            "workspace": alpha_workspace,
        },
        "beta": {
            "tenant": beta_tenant,
            "workspace": beta_workspace,
        },
    }


@pytest.fixture
def populated_alpha_workspace(
    session: Session, embedding_service: EmbeddingService, alpha_and_beta_workspaces
) -> dict:
    """Populate Alpha workspace with diverse banking rules."""
    alpha_ws = alpha_and_beta_workspaces["alpha"]["workspace"]

    # Create multiple knowledge bases per workspace (realistic scenario)
    knowledge_bases = []
    for i in range(2):
        kb = WorkflowKnowledge(
            id=_uid(),
            workspace_id=alpha_ws.id,
            workflow_name=f"test_phase3d_alpha_loan_flow_{i}_{_uid()}",
            summary=f"Alpha loan processing workflow {i}",
        )
        session.add(kb)
        session.flush()
        knowledge_bases.append(kb)

    # Define diverse synthetic banking rules
    rule_definitions = [
        # Credit score rules
        {
            "rule": "test_phase3d_IF credit score ABOVE 750 THEN auto-approve personal loan",
            "condition": "credit_score > 750",
            "outcome": "auto_approve_loan",
            "responsible_role": "credit_officer",
            "threshold": "750",
            "kb_index": 0,
        },
        {
            "rule": "test_phase3d_IF credit score BETWEEN 650 and 750 THEN manual review required",
            "condition": "credit_score >= 650 AND credit_score <= 750",
            "outcome": "manual_review",
            "responsible_role": "credit_officer",
            "threshold": "650-750",
            "kb_index": 0,
        },
        # Income rules
        {
            "rule": "test_phase3d_annual income MUST EXCEED 50000 dollars",
            "condition": "annual_income > 50000",
            "outcome": "income_requirement_met",
            "responsible_role": "financial_analyst",
            "threshold": "50000",
            "kb_index": 1,
        },
        # Debt-to-income rules
        {
            "rule": "test_phase3d_debt-to-income ratio CANNOT EXCEED 43 percent",
            "condition": "debt_to_income_ratio <= 0.43",
            "outcome": "debt_ratio_acceptable",
            "responsible_role": "financial_analyst",
            "threshold": "0.43",
            "kb_index": 1,
        },
        # Employment rules
        {
            "rule": "test_phase3d_employment duration MUST BE at least 2 years",
            "condition": "employment_duration_months >= 24",
            "outcome": "employment_stable",
            "responsible_role": "hr_specialist",
            "threshold": "24",
            "kb_index": 0,
        },
        # Collateral rules
        {
            "rule": "test_phase3d_collateral value MUST EXCEED loan amount BY minimum 20 percent",
            "condition": "collateral_value >= loan_amount * 1.2",
            "outcome": "collateral_sufficient",
            "responsible_role": "appraiser",
            "threshold": "1.2",
            "kb_index": 1,
        },
    ]

    rules = []
    for rule_def in rule_definitions:
        kb = knowledge_bases[rule_def["kb_index"]]
        rule = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=kb.id,
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

    return {
        "workspace": alpha_ws,
        "knowledge_bases": knowledge_bases,
        "rules": rules,
        "tenant": alpha_and_beta_workspaces["alpha"]["tenant"],
    }


class TestHybridRetrievalEndToEnd:
    """End-to-end hybrid retrieval validation."""

    def test_complete_retrieval_pipeline(
        self, session: Session, embedding_service: EmbeddingService, populated_alpha_workspace
    ):
        """Verify complete pipeline: query → vector → BM25 → FTS → RRF → results."""
        alpha_data = populated_alpha_workspace
        workspace = alpha_data["workspace"]

        # Initialize retrievers
        repo = RuleRepository(session)
        vector_retriever = RuleVectorRetriever(repo, workspace_id=workspace.id)
        bm25_retriever = RuleKeywordRetriever(repo, workspace_id=workspace.id)
        postgres_retriever = RulePostgresRetriever(repo, workspace_id=workspace.id)
        fusion = RuleReciprocalRankFusion(session, workspace_id=workspace.id)

        # Query for loan approval rules
        query_text = "credit score approval requirements"
        query_embedding = embedding_service.generate_embedding(query_text)

        # Run all three channels
        vector_results = vector_retriever.search(embedding=query_embedding, limit=20)
        bm25_results = bm25_retriever.search(query=query_text, limit=20)
        postgres_results = postgres_retriever.search(query=query_text, limit=20)

        # Fuse results
        fused = fusion.fuse(
            vector_results=vector_results,
            bm25_results=bm25_results,
            postgres_results=postgres_results,
            top_k=10,
        )

        # Verify results
        assert len(fused) > 0, "Pipeline should return fused results"
        assert all(hasattr(r, 'rule') for r in fused), "Results should have rule attribute"
        assert all(hasattr(r, 'rrf_score') for r in fused), "Results should have RRF score"

        # Verify all results are from the requested workspace
        for result in fused:
            kb = session.query(WorkflowKnowledge).filter_by(
                id=result.rule.workflow_knowledge_id
            ).first()
            assert kb.workspace_id == workspace.id

    def test_multi_channel_deduplication(
        self, session: Session, embedding_service: EmbeddingService, populated_alpha_workspace
    ):
        """Verify that same rule from multiple channels appears only once."""
        alpha_data = populated_alpha_workspace
        workspace = alpha_data["workspace"]

        repo = RuleRepository(session)
        vector_retriever = RuleVectorRetriever(repo, workspace_id=workspace.id)
        bm25_retriever = RuleKeywordRetriever(repo, workspace_id=workspace.id)
        postgres_retriever = RulePostgresRetriever(repo, workspace_id=workspace.id)
        fusion = RuleReciprocalRankFusion(session, workspace_id=workspace.id)

        query_text = "credit score"
        query_embedding = embedding_service.generate_embedding(query_text)

        vector_results = vector_retriever.search(embedding=query_embedding, limit=20)
        bm25_results = bm25_retriever.search(query=query_text, limit=20)
        postgres_results = postgres_retriever.search(query=query_text, limit=20)

        fused = fusion.fuse(
            vector_results=vector_results,
            bm25_results=bm25_results,
            postgres_results=postgres_results,
            top_k=20,
        )

        # Check for duplicates
        fused_ids = [r.rule.id for r in fused]
        assert len(fused_ids) == len(set(fused_ids)), "No duplicate rule IDs in fused results"

    def test_channel_ranking_preserved(
        self, session: Session, embedding_service: EmbeddingService, populated_alpha_workspace
    ):
        """Verify that individual channel ranks are preserved in fusion output."""
        alpha_data = populated_alpha_workspace
        workspace = alpha_data["workspace"]

        repo = RuleRepository(session)
        vector_retriever = RuleVectorRetriever(repo, workspace_id=workspace.id)
        bm25_retriever = RuleKeywordRetriever(repo, workspace_id=workspace.id)
        postgres_retriever = RulePostgresRetriever(repo, workspace_id=workspace.id)
        fusion = RuleReciprocalRankFusion(session, workspace_id=workspace.id)

        query_text = "credit score income"
        query_embedding = embedding_service.generate_embedding(query_text)

        vector_results = vector_retriever.search(embedding=query_embedding, limit=20)
        bm25_results = bm25_retriever.search(query=query_text, limit=20)
        postgres_results = postgres_retriever.search(query=query_text, limit=20)

        fused = fusion.fuse(
            vector_results=vector_results,
            bm25_results=bm25_results,
            postgres_results=postgres_results,
            top_k=10,
        )

        # Verify channel ranks are preserved
        for result in fused:
            # At least one channel should have ranked this rule
            has_rank = (
                result.vector_rank is not None
                or result.bm25_rank is not None
                or result.postgres_rank is not None
            )
            assert has_rank, f"Rule {result.rule.id} should have at least one channel rank"

            # Original scores should be preserved
            if result.vector_rank is not None:
                assert result.vector_score is not None, "Vector score should be preserved"
            if result.bm25_rank is not None:
                assert result.bm25_score is not None, "BM25 score should be preserved"
            if result.postgres_rank is not None:
                assert result.postgres_score is not None, "Postgres score should be preserved"


class TestTenantWorkspaceIsolation:
    """Verify tenant and workspace isolation at response boundary."""

    def test_alpha_cannot_retrieve_beta_rules(
        self, session: Session, embedding_service: EmbeddingService, alpha_and_beta_workspaces
    ):
        """Verify Alpha workspace cannot retrieve Beta workspace rules."""
        alpha_ws = alpha_and_beta_workspaces["alpha"]["workspace"]
        beta_ws = alpha_and_beta_workspaces["beta"]["workspace"]

        # Add rules to Beta workspace
        beta_knowledge = WorkflowKnowledge(
            id=_uid(),
            workspace_id=beta_ws.id,
            workflow_name=f"test_phase3d_beta_iso_{_uid()}",
            summary="Beta isolation test",
        )
        session.add(beta_knowledge)
        session.flush()

        beta_rule = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=beta_knowledge.id,
            rule="test_phase3d_beta-only credit scoring rule",
            condition="credit_score > 700",
        )
        embedding = embedding_service.generate_embedding("credit score")
        beta_rule.embedding = embedding
        session.add(beta_rule)
        session.commit()

        # Try to retrieve from Alpha workspace
        repo = RuleRepository(session)
        vector_retriever = RuleVectorRetriever(repo, workspace_id=alpha_ws.id)
        bm25_retriever = RuleKeywordRetriever(repo, workspace_id=alpha_ws.id)
        postgres_retriever = RulePostgresRetriever(repo, workspace_id=alpha_ws.id)

        query_embedding = embedding_service.generate_embedding("credit score")
        vector_results = vector_retriever.search(embedding=query_embedding, limit=20)
        bm25_results = bm25_retriever.search(query="credit score", limit=20)
        postgres_results = postgres_retriever.search(query="credit score", limit=20)

        # None should contain Beta rule
        all_ids = (
            {r.entity.id for r in vector_results}
            | {r.entity.id for r in bm25_results}
            | {r.entity.id for r in postgres_results}
        )

        assert beta_rule.id not in all_ids, "Beta rule should not be retrievable from Alpha workspace"

    def test_cross_workspace_result_rejected_by_fusion(
        self, session: Session, alpha_and_beta_workspaces
    ):
        """Verify RRF rejects results from unexpected workspace."""
        from app.retrieval.models import RetrievalCandidate

        alpha_ws = alpha_and_beta_workspaces["alpha"]["workspace"]
        beta_ws = alpha_and_beta_workspaces["beta"]["workspace"]

        # Create rule in Beta workspace
        beta_knowledge = WorkflowKnowledge(
            id=_uid(),
            workspace_id=beta_ws.id,
            workflow_name=f"test_phase3d_fusion_iso_{_uid()}",
            summary="Fusion isolation test",
        )
        session.add(beta_knowledge)
        session.flush()

        beta_rule = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=beta_knowledge.id,
            rule="test_phase3d_beta rule",
            condition="cond",
        )
        session.add(beta_rule)
        session.commit()

        # Try to fuse Beta rule as if it came from Alpha retrieval
        fusion = RuleReciprocalRankFusion(session, workspace_id=alpha_ws.id)
        cross_ws_candidate = RetrievalCandidate(
            entity=beta_rule, score=0.9, source="vector"
        )

        # Should raise ValueError
        with pytest.raises(ValueError, match="belongs to workspace"):
            fusion.fuse(
                vector_results=[cross_ws_candidate],
                bm25_results=[],
                postgres_results=[],
                top_k=10,
            )

    def test_tenant_validation_on_fusion_init(
        self, session: Session, alpha_and_beta_workspaces
    ):
        """Verify tenant_id validation at fusion initialization."""
        alpha_ws = alpha_and_beta_workspaces["alpha"]["workspace"]
        beta_tenant = alpha_and_beta_workspaces["beta"]["tenant"]

        # Try to initialize fusion for Alpha workspace with Beta tenant
        with pytest.raises(ValueError, match="does not belong to tenant"):
            RuleReciprocalRankFusion(
                session,
                workspace_id=alpha_ws.id,
                tenant_id=beta_tenant.id,
            )


class TestRegressionAndFailureHandling:
    """Test edge cases and failure scenarios."""

    def test_missing_embeddings_excluded_from_vector_search(
        self, session: Session, embedding_service: EmbeddingService, populated_alpha_workspace
    ):
        """Verify that rules without embeddings are excluded from vector search."""
        alpha_data = populated_alpha_workspace
        workspace = alpha_data["workspace"]
        knowledge = alpha_data["knowledge_bases"][0]

        # Add rule without embedding
        rule_no_embedding = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge.id,
            rule="test_phase3d_rule without embedding",
            condition="test_condition",
        )
        session.add(rule_no_embedding)
        session.commit()

        repo = RuleRepository(session)
        vector_retriever = RuleVectorRetriever(repo, workspace_id=workspace.id)

        query_embedding = embedding_service.generate_embedding("test")
        results = vector_retriever.search(embedding=query_embedding, limit=20)

        result_ids = {r.entity.id for r in results}
        assert rule_no_embedding.id not in result_ids, "Rule without embedding should be excluded"

    def test_empty_workspace_returns_empty_results(
        self, session: Session, embedding_service: EmbeddingService, alpha_and_beta_workspaces
    ):
        """Verify that empty workspace returns empty results."""
        # Create empty workspace (no rules, no knowledge)
        empty_ws = Workspace(
            id=_uid(),
            tenant_id=alpha_and_beta_workspaces["alpha"]["tenant"].id,
            name=f"test_phase3d_empty_{_uid()}",
            display_name="Empty Workspace",
            active=True,
        )
        session.add(empty_ws)
        session.commit()

        repo = RuleRepository(session)
        vector_retriever = RuleVectorRetriever(repo, workspace_id=empty_ws.id)
        bm25_retriever = RuleKeywordRetriever(repo, workspace_id=empty_ws.id)
        postgres_retriever = RulePostgresRetriever(repo, workspace_id=empty_ws.id)
        fusion = RuleReciprocalRankFusion(session, workspace_id=empty_ws.id)

        query_embedding = embedding_service.generate_embedding("test")
        vector_results = vector_retriever.search(embedding=query_embedding, limit=20)
        bm25_results = bm25_retriever.search(query="test", limit=20)
        postgres_results = postgres_retriever.search(query="test", limit=20)

        assert len(vector_results) == 0
        assert len(bm25_results) == 0
        assert len(postgres_results) == 0

        fused = fusion.fuse(
            vector_results=vector_results,
            bm25_results=bm25_results,
            postgres_results=postgres_results,
            top_k=20,
        )

        assert len(fused) == 0, "Empty workspace should return empty fused results"

    def test_empty_query_returns_empty_results(
        self, session: Session, populated_alpha_workspace
    ):
        """Verify that empty query returns empty results."""
        alpha_data = populated_alpha_workspace
        workspace = alpha_data["workspace"]

        repo = RuleRepository(session)
        bm25_retriever = RuleKeywordRetriever(repo, workspace_id=workspace.id)
        postgres_retriever = RulePostgresRetriever(repo, workspace_id=workspace.id)

        bm25_results = bm25_retriever.search(query="", limit=20)
        postgres_results = postgres_retriever.search(query="", limit=20)

        assert len(bm25_results) == 0
        assert len(postgres_results) == 0

    def test_single_channel_failure_does_not_break_pipeline(
        self, session: Session, embedding_service: EmbeddingService, populated_alpha_workspace
    ):
        """Verify that missing one channel doesn't break the pipeline."""
        alpha_data = populated_alpha_workspace
        workspace = alpha_data["workspace"]

        repo = RuleRepository(session)
        vector_retriever = RuleVectorRetriever(repo, workspace_id=workspace.id)
        postgres_retriever = RulePostgresRetriever(repo, workspace_id=workspace.id)
        fusion = RuleReciprocalRankFusion(session, workspace_id=workspace.id)

        query_text = "credit score"
        query_embedding = embedding_service.generate_embedding(query_text)

        vector_results = vector_retriever.search(embedding=query_embedding, limit=20)
        postgres_results = postgres_retriever.search(query=query_text, limit=20)

        # Fuse without BM25 (empty channel)
        fused = fusion.fuse(
            vector_results=vector_results,
            bm25_results=[],  # Missing channel
            postgres_results=postgres_results,
            top_k=10,
        )

        # Should still produce results from vector + postgres
        assert len(fused) > 0 or (len(vector_results) == 0 and len(postgres_results) == 0)

    def test_deterministic_ordering(
        self, session: Session, embedding_service: EmbeddingService, populated_alpha_workspace
    ):
        """Verify that identical queries produce identical result ordering."""
        alpha_data = populated_alpha_workspace
        workspace = alpha_data["workspace"]

        repo = RuleRepository(session)
        vector_retriever = RuleVectorRetriever(repo, workspace_id=workspace.id)
        bm25_retriever = RuleKeywordRetriever(repo, workspace_id=workspace.id)
        postgres_retriever = RulePostgresRetriever(repo, workspace_id=workspace.id)
        fusion = RuleReciprocalRankFusion(session, workspace_id=workspace.id)

        query_text = "credit score income"
        query_embedding = embedding_service.generate_embedding(query_text)

        # Run pipeline twice
        run1_ids = []
        run2_ids = []

        for _ in range(2):
            vector_results = vector_retriever.search(embedding=query_embedding, limit=20)
            bm25_results = bm25_retriever.search(query=query_text, limit=20)
            postgres_results = postgres_retriever.search(query=query_text, limit=20)

            fused = fusion.fuse(
                vector_results=vector_results,
                bm25_results=bm25_results,
                postgres_results=postgres_results,
                top_k=10,
            )

            result_ids = [r.rule.id for r in fused]
            if len(run1_ids) == 0:
                run1_ids = result_ids
            else:
                run2_ids = result_ids

        # Results should be identical
        assert run1_ids == run2_ids, "Identical queries should produce identical result ordering"


class TestPerformanceBaseline:
    """Record performance baselines (not optimization targets)."""

    def test_retrieval_latency_baseline(
        self, session: Session, embedding_service: EmbeddingService, populated_alpha_workspace
    ):
        """Record latency for each retrieval channel and RRF fusion."""
        alpha_data = populated_alpha_workspace
        workspace = alpha_data["workspace"]

        repo = RuleRepository(session)
        vector_retriever = RuleVectorRetriever(repo, workspace_id=workspace.id)
        bm25_retriever = RuleKeywordRetriever(repo, workspace_id=workspace.id)
        postgres_retriever = RulePostgresRetriever(repo, workspace_id=workspace.id)
        fusion = RuleReciprocalRankFusion(session, workspace_id=workspace.id)

        query_text = "credit score income debt"
        query_embedding = embedding_service.generate_embedding(query_text)

        # Measure vector retrieval latency
        start = time.time()
        vector_results = vector_retriever.search(embedding=query_embedding, limit=20)
        vector_latency = time.time() - start

        # Measure BM25 retrieval latency
        start = time.time()
        bm25_results = bm25_retriever.search(query=query_text, limit=20)
        bm25_latency = time.time() - start

        # Measure PostgreSQL FTS latency
        start = time.time()
        postgres_results = postgres_retriever.search(query=query_text, limit=20)
        postgres_latency = time.time() - start

        # Measure RRF fusion latency
        start = time.time()
        fused = fusion.fuse(
            vector_results=vector_results,
            bm25_results=bm25_results,
            postgres_results=postgres_results,
            top_k=10,
        )
        fusion_latency = time.time() - start

        total_latency = vector_latency + bm25_latency + postgres_latency + fusion_latency

        # Record for reporting (not assertions)
        print(f"\n=== Hybrid Retrieval Latency Baseline ===")
        print(f"Vector retrieval:     {vector_latency*1000:.2f}ms")
        print(f"BM25 retrieval:       {bm25_latency*1000:.2f}ms")
        print(f"PostgreSQL FTS:       {postgres_latency*1000:.2f}ms")
        print(f"RRF fusion:           {fusion_latency*1000:.2f}ms")
        print(f"Total pipeline:       {total_latency*1000:.2f}ms")
        print(f"Result count:         {len(fused)}")
        print(f"Alpha workspace has:  {len(alpha_data['rules'])} rules")
        print(f"Dataset size:         {len(alpha_data['knowledge_bases'])} knowledge bases")

        # Basic sanity checks
        assert vector_latency > 0, "Vector retrieval should take measurable time"
        assert bm25_latency > 0, "BM25 retrieval should take measurable time"
        assert postgres_latency > 0, "PostgreSQL FTS should take measurable time"
        assert fusion_latency > 0, "RRF fusion should take measurable time"
