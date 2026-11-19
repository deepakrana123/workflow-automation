"""
Phase 3A: Workspace-Scoped Business Rule Vector Retrieval

Test suite for semantic vector-based retrieval of WorkflowBusinessRule records.

Validates:
1. Vector search returns semantically relevant rules
2. Workspace isolation is preserved
3. Cross-tenant retrieval is impossible
4. Missing embeddings are excluded
5. Top-k limits are respected
6. Source provenance is maintained
7. Result contracts match specification
"""

import pytest
from typing import Any
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.workspace import Workspace
from app.models.tenant import Tenant
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workflow_business_rule import WorkflowBusinessRule

from app.knowledge_ingestions.rule_repository import RuleRepository
from app.retrieval.rule_vector_retriever import RuleVectorRetriever
from app.semantic.embedding_service import EmbeddingService
from app.retrieval.models import RetrievalCandidate


def _uid() -> int:
    """Generate unique random ID."""
    return uuid.uuid4().int % (2**31 - 1)


@pytest.fixture
def session() -> Session:
    """Database session for integration tests."""
    session = SessionLocal()
    yield session
    # Cleanup: delete test-owned records
    test_pattern = "test_phase3a_%"
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
        name=f"test_phase3a_tenant_{_uid()}",
        slug=f"test-phase3a-{_uid()}",
        display_name="Test Phase 3A Tenant",
        active=True,
    )
    session.add(tenant)
    session.flush()

    workspace = Workspace(
        id=_uid(),
        tenant_id=tenant.id,
        name=f"test_phase3a_workspace_{_uid()}",
        display_name="Test Phase 3A Workspace",
        active=True,
    )
    session.add(workspace)
    session.commit()

    return workspace, tenant


@pytest.fixture
def test_workspace_with_rules(
    session: Session, embedding_service: EmbeddingService, test_workspace
) -> tuple[Workspace, list[WorkflowBusinessRule]]:
    """Create a workspace with diverse business rules and their embeddings."""
    workspace, tenant = test_workspace

    # Create knowledge base
    knowledge = WorkflowKnowledge(
        id=_uid(),
        workspace_id=workspace.id,
        workflow_name=f"test_phase3a_loan_flow_{_uid()}",
        summary="Test loan processing workflow",
    )
    session.add(knowledge)
    session.flush()

    # Define diverse rules for semantic testing
    rule_definitions = [
        {
            "rule": "test_phase3a_if credit score above 700 then approve",
            "condition": "credit_score > 700",
            "outcome": "approve_loan",
            "responsible_role": "credit_officer",
            "threshold": None,
        },
        {
            "rule": "test_phase3a_if debt ratio below 50 percent then accept",
            "condition": "debt_ratio < 0.5",
            "outcome": "accept_application",
            "responsible_role": "underwriter",
            "threshold": "0.5",
        },
        {
            "rule": "test_phase3a_if annual income above 50000 and credit score above 650 then consider",
            "condition": "income > 50000 AND credit_score > 650",
            "outcome": "consider_for_approval",
            "responsible_role": "loan_manager",
            "threshold": None,
        },
        {
            "rule": "test_phase3a_employment stability check must pass",
            "condition": "employment_duration_months > 12",
            "outcome": "pass_stability_check",
            "responsible_role": "hr_specialist",
            "threshold": "12",
        },
        {
            "rule": "test_phase3a_collateral must exceed loan amount by 20 percent",
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

        # Generate embedding for each rule
        rule_text = embedding_service.build_rule_text(rule)
        embedding = embedding_service.generate_embedding(rule_text)
        rule.embedding = embedding
        rule.embedding_model_name = "BAAI/bge-small-en-v1.5"
        rule.embedding_model_version = "1.5"

        session.add(rule)
        rules.append(rule)

    session.commit()
    return workspace, rules


class TestBusinessRuleVectorSearch:
    """Test vector-based semantic search for WorkflowBusinessRule."""

    def test_vector_retrieval_returns_similar_rules(
        self, session: Session, embedding_service: EmbeddingService, test_workspace_with_rules
    ):
        """Verify that vector search returns semantically similar rules."""
        workspace, rules = test_workspace_with_rules

        # Query: "what is the minimum credit score requirement?"
        query_text = "credit score requirement minimum approval"
        query_embedding = embedding_service.generate_embedding(query_text)

        repo = RuleRepository(session)
        results = repo.search_by_embedding(
            workspace_id=workspace.id,
            embedding=query_embedding,
            limit=5,
        )

        # Should find rules related to credit score
        assert len(results) > 0, "Should find at least one rule"
        assert len(results) <= 5, "Should respect limit"

        # First result should be related to credit score
        top_rule, distance = results[0]
        assert top_rule.rule is not None
        assert "credit" in top_rule.rule.lower() or "score" in top_rule.rule.lower()
        assert distance >= 0, "Distance should be non-negative"

    def test_retrieval_excludes_missing_embeddings(
        self, session: Session, embedding_service: EmbeddingService, test_workspace
    ):
        """Verify that rules without embeddings are excluded from results."""
        workspace, tenant = test_workspace

        # Create knowledge base
        knowledge = WorkflowKnowledge(
            id=_uid(),
            workspace_id=workspace.id,
            workflow_name=f"test_phase3a_wf_no_emb_{_uid()}",
            summary="Workflow without embeddings",
        )
        session.add(knowledge)
        session.flush()

        # Create rules with and without embeddings
        rule_with_embedding = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge.id,
            rule="test_phase3a_rule with embedding",
            condition="condition1",
        )
        embedding = embedding_service.generate_embedding("test rule")
        rule_with_embedding.embedding = embedding

        rule_without_embedding = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge.id,
            rule="test_phase3a_rule without embedding",
            condition="condition2",
        )
        # Explicitly do NOT set embedding

        session.add(rule_with_embedding)
        session.add(rule_without_embedding)
        session.commit()

        # Search should only return rule with embedding
        query_embedding = embedding_service.generate_embedding("test")
        repo = RuleRepository(session)
        results = repo.search_by_embedding(
            workspace_id=workspace.id,
            embedding=query_embedding,
            limit=10,
        )

        result_ids = {rule.id for rule, _ in results}
        assert rule_with_embedding.id in result_ids
        assert rule_without_embedding.id not in result_ids

    def test_workspace_isolation_in_vector_search(
        self, session: Session, embedding_service: EmbeddingService
    ):
        """Verify that vector search respects workspace boundaries."""
        # Create two separate workspaces with different tenants
        tenant1 = Tenant(
            id=_uid(),
            name=f"test_phase3a_tenant1_{_uid()}",
            slug=f"test-phase3a-1-{_uid()}",
            display_name="Tenant 1",
            active=True,
        )
        session.add(tenant1)
        session.flush()

        workspace1 = Workspace(
            id=_uid(),
            tenant_id=tenant1.id,
            name=f"test_phase3a_ws1_{_uid()}",
            display_name="Workspace 1",
            active=True,
        )
        session.add(workspace1)
        session.flush()

        tenant2 = Tenant(
            id=_uid(),
            name=f"test_phase3a_tenant2_{_uid()}",
            slug=f"test-phase3a-2-{_uid()}",
            display_name="Tenant 2",
            active=True,
        )
        session.add(tenant2)
        session.flush()

        workspace2 = Workspace(
            id=_uid(),
            tenant_id=tenant2.id,
            name=f"test_phase3a_ws2_{_uid()}",
            display_name="Workspace 2",
            active=True,
        )
        session.add(workspace2)
        session.commit()

        # Create identical rules in each workspace
        knowledge1 = WorkflowKnowledge(
            id=_uid(),
            workspace_id=workspace1.id,
            workflow_name=f"test_phase3a_flow_iso1_{_uid()}",
            summary="Workflow 1",
        )
        session.add(knowledge1)
        session.flush()

        knowledge2 = WorkflowKnowledge(
            id=_uid(),
            workspace_id=workspace2.id,
            workflow_name=f"test_phase3a_flow_iso2_{_uid()}",
            summary="Workflow 2",
        )
        session.add(knowledge2)
        session.flush()

        rule_text = "test_phase3a_identical rule for isolation testing"
        embedding = embedding_service.generate_embedding(rule_text)

        rule1 = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge1.id,
            rule=rule_text,
            condition="cond1",
        )
        rule1.embedding = embedding

        rule2 = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge2.id,
            rule=rule_text,
            condition="cond2",
        )
        rule2.embedding = embedding

        session.add(rule1)
        session.add(rule2)
        session.commit()

        # Search in workspace1 should only return rule1
        repo = RuleRepository(session)
        results_ws1 = repo.search_by_embedding(
            workspace_id=workspace1.id,
            embedding=embedding,
            limit=10,
        )
        result_ids_ws1 = {rule.id for rule, _ in results_ws1}

        assert rule1.id in result_ids_ws1
        assert rule2.id not in result_ids_ws1

        # Search in workspace2 should only return rule2
        results_ws2 = repo.search_by_embedding(
            workspace_id=workspace2.id,
            embedding=embedding,
            limit=10,
        )
        result_ids_ws2 = {rule.id for rule, _ in results_ws2}

        assert rule2.id in result_ids_ws2
        assert rule1.id not in result_ids_ws2

    def test_top_k_limit_is_respected(
        self, session: Session, embedding_service: EmbeddingService, test_workspace
    ):
        """Verify that top_k parameter limits results correctly."""
        workspace, tenant = test_workspace

        knowledge = WorkflowKnowledge(
            id=_uid(),
            workspace_id=workspace.id,
            workflow_name=f"test_phase3a_topk_{_uid()}",
            summary="Test top-k limit",
        )
        session.add(knowledge)
        session.flush()

        # Create 10 rules
        embedding_base = embedding_service.generate_embedding("test")
        for i in range(10):
            rule = WorkflowBusinessRule(
                id=_uid(),
                workflow_knowledge_id=knowledge.id,
                rule=f"test_phase3a_rule {i}",
                condition=f"condition_{i}",
            )
            rule.embedding = embedding_base  # Same embedding for all
            session.add(rule)

        session.commit()

        repo = RuleRepository(session)

        # Test various limits
        for limit in [1, 3, 5, 10, 20]:
            results = repo.search_by_embedding(
                workspace_id=workspace.id,
                embedding=embedding_base,
                limit=limit,
            )
            assert (
                len(results) <= limit
            ), f"Results {len(results)} should not exceed limit {limit}"

    def test_result_contract_contains_required_fields(
        self, session: Session, embedding_service: EmbeddingService, test_workspace_with_rules
    ):
        """Verify that results contain all required provenance fields."""
        workspace, rules = test_workspace_with_rules

        query_embedding = embedding_service.generate_embedding("test query")
        repo = RuleRepository(session)
        results = repo.search_by_embedding(
            workspace_id=workspace.id,
            embedding=query_embedding,
            limit=5,
        )

        assert len(results) > 0
        rule, distance = results[0]

        # Check required fields exist
        assert rule.id is not None
        assert rule.rule is not None
        assert rule.workflow_knowledge_id is not None
        assert distance is not None and isinstance(distance, (int, float))

        # Check optional provenance fields exist (may be None)
        assert hasattr(rule, "condition")
        assert hasattr(rule, "outcome")
        assert hasattr(rule, "responsible_role")
        assert hasattr(rule, "threshold")
        assert hasattr(rule, "source_brd_document_id")

    def test_retrieval_candidate_wrapper(
        self, session: Session, embedding_service: EmbeddingService, test_workspace_with_rules
    ):
        """Verify RetrievalCandidate wrapper correctly formats results."""
        workspace, rules = test_workspace_with_rules

        query_embedding = embedding_service.generate_embedding("credit score")
        retriever = RuleVectorRetriever(
            RuleRepository(session), workspace_id=workspace.id
        )
        results = retriever.search(embedding=query_embedding, limit=5)

        assert len(results) > 0
        assert all(isinstance(r, RetrievalCandidate) for r in results)

        candidate = results[0]
        assert candidate.entity is not None
        assert isinstance(candidate.entity, WorkflowBusinessRule)
        assert candidate.score is not None and isinstance(candidate.score, float)
        assert candidate.source == "vector"

    def test_empty_workspace_returns_empty_results(
        self, session: Session, embedding_service: EmbeddingService, test_workspace
    ):
        """Verify that searching in empty workspace returns no results."""
        workspace, tenant = test_workspace

        # Don't add any knowledge or rules to this workspace
        query_embedding = embedding_service.generate_embedding("any query")
        repo = RuleRepository(session)
        results = repo.search_by_embedding(
            workspace_id=workspace.id,
            embedding=query_embedding,
            limit=10,
        )

        assert len(results) == 0

    def test_allowed_ids_filtering(
        self, session: Session, embedding_service: EmbeddingService, test_workspace_with_rules
    ):
        """Verify that allowed_ids parameter filters results at SQL level."""
        workspace, rules = test_workspace_with_rules

        # Select subset of rule IDs to allow
        allowed_rule_ids = {rules[0].id, rules[1].id}

        query_embedding = embedding_service.generate_embedding("test")
        repo = RuleRepository(session)
        results = repo.search_by_embedding(
            workspace_id=workspace.id,
            embedding=query_embedding,
            limit=10,
            allowed_ids=allowed_rule_ids,
        )

        result_ids = {rule.id for rule, _ in results}
        assert result_ids.issubset(
            allowed_rule_ids
        ), "All results should be in allowed_ids"

    def test_empty_allowed_ids_returns_empty(
        self, session: Session, embedding_service: EmbeddingService, test_workspace_with_rules
    ):
        """Verify that empty allowed_ids returns no results (guard clause)."""
        workspace, rules = test_workspace_with_rules

        query_embedding = embedding_service.generate_embedding("test")
        repo = RuleRepository(session)
        results = repo.search_by_embedding(
            workspace_id=workspace.id,
            embedding=query_embedding,
            limit=10,
            allowed_ids=set(),  # Empty set
        )

        assert len(results) == 0

    def test_build_rule_text_concatenates_fields(
        self, session: Session, embedding_service: EmbeddingService
    ):
        """Verify that build_rule_text correctly constructs searchable text."""
        rule = WorkflowBusinessRule(
            id=1,
            workflow_knowledge_id=1,
            rule="if debt ratio below 50 percent",
            condition="debt_ratio < 0.5",
            outcome="accept_application",
            responsible_role="underwriter",
            threshold="0.5",
        )

        text = embedding_service.build_rule_text(rule)

        # All fields should appear in output
        assert "debt ratio" in text.lower()
        assert "0.5" in text
        assert "accept_application" in text
        assert "underwriter" in text

    def test_embedding_dimensions_match(
        self, session: Session, embedding_service: EmbeddingService, test_workspace_with_rules
    ):
        """Verify that generated embeddings match stored dimensions (384)."""
        workspace, rules = test_workspace_with_rules

        for rule in rules:
            assert len(rule.embedding) == 384, f"Rule {rule.id} embedding dimension: {len(rule.embedding)}"

    def test_query_embedding_matches_stored_format(
        self, session: Session, embedding_service: EmbeddingService, test_workspace_with_rules
    ):
        """Verify that query embeddings can be compared to stored embeddings."""
        workspace, rules = test_workspace_with_rules

        query_text = "credit score approval"
        query_embedding = embedding_service.generate_embedding(query_text)

        # Query embedding should be same dimension
        assert len(query_embedding) == 384

        # Should be retrievable by cosine distance
        repo = RuleRepository(session)
        results = repo.search_by_embedding(
            workspace_id=workspace.id,
            embedding=query_embedding,
            limit=5,
        )

        assert len(results) > 0
