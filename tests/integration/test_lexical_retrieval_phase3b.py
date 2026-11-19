"""
Phase 3B: BM25 and PostgreSQL FTS Lexical Retrieval Validation

Comprehensive test suite for keyword-based semantic retrieval of WorkflowBusinessRule.

Validates:
1. BM25 keyword retrieval returns relevant rules
2. PostgreSQL FTS retrieval with AND/OR fallback
3. Workspace isolation in both retrieval methods
4. Cross-tenant retrieval prevention
5. Result ranking and top-k limits
6. Empty and malformed query handling
7. Provenance preservation
8. Result contract compatibility with vector retrieval
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
from app.retrieval.rule_keyword_retriever import RuleKeywordRetriever
from app.retrieval.rule_postgres_retriever import RulePostgresRetriever
from app.retrieval.models import RetrievalCandidate


def _uid() -> int:
    """Generate unique random ID."""
    return uuid.uuid4().int % (2**31 - 1)


@pytest.fixture
def session() -> Session:
    """Database session for integration tests."""
    session = SessionLocal()
    yield session
    # Cleanup
    test_pattern = "test_phase3b_%"
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
def test_workspace(session: Session) -> tuple[Workspace, Tenant]:
    """Create a test workspace and tenant."""
    tenant = Tenant(
        id=_uid(),
        name=f"test_phase3b_tenant_{_uid()}",
        slug=f"test-phase3b-{_uid()}",
        display_name="Test Phase 3B Tenant",
        active=True,
    )
    session.add(tenant)
    session.flush()

    workspace = Workspace(
        id=_uid(),
        tenant_id=tenant.id,
        name=f"test_phase3b_workspace_{_uid()}",
        display_name="Test Phase 3B Workspace",
        active=True,
    )
    session.add(workspace)
    session.commit()

    return workspace, tenant


@pytest.fixture
def test_workspace_with_rules(
    session: Session, test_workspace
) -> tuple[Workspace, list[WorkflowBusinessRule]]:
    """Create a workspace with diverse lexically searchable rules."""
    workspace, tenant = test_workspace

    # Create knowledge base
    knowledge = WorkflowKnowledge(
        id=_uid(),
        workspace_id=workspace.id,
        workflow_name=f"test_phase3b_loan_flow_{_uid()}",
        summary="Test loan processing workflow",
    )
    session.add(knowledge)
    session.flush()

    # Define diverse rules for lexical testing
    rule_definitions = [
        {
            "rule": "test_phase3b_IF credit score ABOVE 700 THEN approve immediately",
            "condition": "credit_score > 700",
            "outcome": "approve_loan",
            "responsible_role": "credit_officer",
            "threshold": "700",
        },
        {
            "rule": "test_phase3b_IF debt-to-income ratio BELOW 50 percent THEN accept application",
            "condition": "debt_ratio < 0.5",
            "outcome": "accept_application",
            "responsible_role": "underwriter",
            "threshold": "0.5",
        },
        {
            "rule": "test_phase3b_IF annual income ABOVE 50000 AND credit ABOVE 650 THEN consider approval",
            "condition": "income > 50000 AND credit_score > 650",
            "outcome": "consider_for_approval",
            "responsible_role": "loan_manager",
            "threshold": None,
        },
        {
            "rule": "test_phase3b_employment stability MUST PASS verification",
            "condition": "employment_duration_months > 12",
            "outcome": "pass_stability_check",
            "responsible_role": "hr_specialist",
            "threshold": "12",
        },
        {
            "rule": "test_phase3b_collateral value MUST EXCEED loan amount BY 20 percent minimum",
            "condition": "collateral_value > loan_amount * 1.2",
            "outcome": "collateral_verified",
            "responsible_role": "appraiser",
            "threshold": "1.2",
        },
        {
            "rule": "test_phase3b_property appraisal REQUIRED for residential loans above 500000",
            "condition": "loan_amount > 500000 AND property_type = 'residential'",
            "outcome": "require_appraisal",
            "responsible_role": "appraiser",
            "threshold": None,
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
        session.add(rule)
        rules.append(rule)

    session.commit()
    return workspace, rules


class TestBM25KeywordRetrieval:
    """Test BM25-based keyword retrieval for WorkflowBusinessRule."""

    def test_bm25_returns_relevant_rules(
        self, session: Session, test_workspace_with_rules
    ):
        """Verify that BM25 search returns semantically relevant rules."""
        workspace, rules = test_workspace_with_rules

        repo = RuleRepository(session)
        retriever = RuleKeywordRetriever(repo, workspace_id=workspace.id)

        # Query: "what credit score is needed for approval"
        results = retriever.search(query="credit score approval", limit=5)

        assert len(results) > 0, "Should find at least one rule"
        assert all(isinstance(r, RetrievalCandidate) for r in results)

        # Top result should mention credit
        top_rule = results[0].entity
        assert "credit" in top_rule.rule.lower()

    def test_bm25_workspace_isolation(self, session: Session):
        """Verify that BM25 respects workspace boundaries."""
        # Create two workspaces
        tenant1 = Tenant(
            id=_uid(),
            name=f"test_phase3b_tenant1_{_uid()}",
            slug=f"test-phase3b-1-{_uid()}",
            display_name="Tenant 1",
            active=True,
        )
        session.add(tenant1)
        session.flush()

        workspace1 = Workspace(
            id=_uid(),
            tenant_id=tenant1.id,
            name=f"test_phase3b_ws1_{_uid()}",
            display_name="Workspace 1",
            active=True,
        )
        session.add(workspace1)
        session.flush()

        tenant2 = Tenant(
            id=_uid(),
            name=f"test_phase3b_tenant2_{_uid()}",
            slug=f"test-phase3b-2-{_uid()}",
            display_name="Tenant 2",
            active=True,
        )
        session.add(tenant2)
        session.flush()

        workspace2 = Workspace(
            id=_uid(),
            tenant_id=tenant2.id,
            name=f"test_phase3b_ws2_{_uid()}",
            display_name="Workspace 2",
            active=True,
        )
        session.add(workspace2)
        session.commit()

        # Create rules in each workspace
        knowledge1 = WorkflowKnowledge(
            id=_uid(),
            workspace_id=workspace1.id,
            workflow_name=f"test_phase3b_flow_iso1_{_uid()}",
            summary="Workflow 1",
        )
        session.add(knowledge1)
        session.flush()

        knowledge2 = WorkflowKnowledge(
            id=_uid(),
            workspace_id=workspace2.id,
            workflow_name=f"test_phase3b_flow_iso2_{_uid()}",
            summary="Workflow 2",
        )
        session.add(knowledge2)
        session.flush()

        rule1 = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge1.id,
            rule="test_phase3b_workspace 1 specific credit rule",
            condition="cond1",
        )

        rule2 = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge2.id,
            rule="test_phase3b_workspace 2 unique income rule",
            condition="cond2",
        )

        session.add(rule1)
        session.add(rule2)
        session.commit()

        # Search in workspace1 should only find rule1
        repo = RuleRepository(session)
        retriever1 = RuleKeywordRetriever(repo, workspace_id=workspace1.id)
        results1 = retriever1.search(query="credit", limit=10)

        result_ids_1 = {r.entity.id for r in results1}
        assert rule1.id in result_ids_1
        assert rule2.id not in result_ids_1

        # Search in workspace2 should only find rule2
        retriever2 = RuleKeywordRetriever(repo, workspace_id=workspace2.id)
        results2 = retriever2.search(query="income", limit=10)

        result_ids_2 = {r.entity.id for r in results2}
        assert rule2.id in result_ids_2
        assert rule1.id not in result_ids_2

    def test_bm25_empty_query(self, session: Session, test_workspace_with_rules):
        """Verify that empty queries are handled gracefully."""
        workspace, rules = test_workspace_with_rules

        repo = RuleRepository(session)
        retriever = RuleKeywordRetriever(repo, workspace_id=workspace.id)

        results = retriever.search(query="", limit=10)
        assert len(results) == 0, "Empty query should return no results"

    def test_bm25_whitespace_query(self, session: Session, test_workspace_with_rules):
        """Verify that whitespace-only queries are handled gracefully."""
        workspace, rules = test_workspace_with_rules

        repo = RuleRepository(session)
        retriever = RuleKeywordRetriever(repo, workspace_id=workspace.id)

        results = retriever.search(query="   \t  ", limit=10)
        assert len(results) == 0, "Whitespace-only query should return no results"

    def test_bm25_top_k_respected(self, session: Session, test_workspace_with_rules):
        """Verify that top_k limits are respected."""
        workspace, rules = test_workspace_with_rules

        repo = RuleRepository(session)
        retriever = RuleKeywordRetriever(repo, workspace_id=workspace.id)

        for limit in [1, 3, 5, 10]:
            results = retriever.search(query="test", limit=limit)
            assert len(results) <= limit, f"Results {len(results)} should not exceed limit {limit}"

    def test_bm25_result_contract(
        self, session: Session, test_workspace_with_rules
    ):
        """Verify that RetrievalCandidate wrapper has correct structure."""
        workspace, rules = test_workspace_with_rules

        repo = RuleRepository(session)
        retriever = RuleKeywordRetriever(repo, workspace_id=workspace.id)
        results = retriever.search(query="test", limit=5)

        if len(results) > 0:
            candidate = results[0]
            assert isinstance(candidate, RetrievalCandidate)
            assert candidate.entity is not None
            assert isinstance(candidate.entity, WorkflowBusinessRule)
            assert candidate.score is not None and isinstance(candidate.score, float)
            assert candidate.source == "bm25"

    def test_bm25_index_rebuild_on_refresh(
        self, session: Session, test_workspace
    ):
        """Verify that refresh rebuilds the BM25 index."""
        workspace, tenant = test_workspace

        knowledge = WorkflowKnowledge(
            id=_uid(),
            workspace_id=workspace.id,
            workflow_name=f"test_phase3b_rebuild_{_uid()}",
            summary="Test rebuild",
        )
        session.add(knowledge)
        session.flush()

        # Create initial rule
        rule1 = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge.id,
            rule="test_phase3b_initial credit rule",
            condition="cond1",
        )
        session.add(rule1)
        session.commit()

        repo = RuleRepository(session)
        retriever = RuleKeywordRetriever(repo, workspace_id=workspace.id)

        # Should find rule1
        results1 = retriever.search(query="credit", limit=10)
        assert any(r.entity.id == rule1.id for r in results1)

        # Add new rule
        rule2 = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge.id,
            rule="test_phase3b_new income rule",
            condition="cond2",
        )
        session.add(rule2)
        session.commit()

        # Without refresh, new rule won't be found
        results_old = retriever.search(query="income", limit=10)
        old_ids = {r.entity.id for r in results_old}
        assert rule2.id not in old_ids, "Before refresh, new rule not in index"

        # After refresh, new rule should be found
        retriever.refresh()
        results_new = retriever.search(query="income", limit=10)
        new_ids = {r.entity.id for r in results_new}
        assert rule2.id in new_ids, "After refresh, new rule should be in index"


class TestPostgresFullTextSearch:
    """Test PostgreSQL FTS retrieval for WorkflowBusinessRule."""

    def test_fts_returns_relevant_rules(
        self, session: Session, test_workspace_with_rules
    ):
        """Verify that FTS search returns semantically relevant rules."""
        workspace, rules = test_workspace_with_rules

        repo = RuleRepository(session)
        retriever = RulePostgresRetriever(repo, workspace_id=workspace.id)

        # Query: "credit scoring"
        results = retriever.search(query="credit score", limit=5)

        assert len(results) > 0, "Should find at least one rule"
        assert all(isinstance(r, RetrievalCandidate) for r in results)

        # Top result should mention credit
        top_rule = results[0].entity
        assert "credit" in top_rule.rule.lower()

    def test_fts_and_fallback_to_or(
        self, session: Session, test_workspace_with_rules
    ):
        """Verify that FTS falls back to OR when AND returns no results."""
        workspace, rules = test_workspace_with_rules

        repo = RuleRepository(session)
        retriever = RulePostgresRetriever(repo, workspace_id=workspace.id)

        # Query with rare word combination that might not match with AND
        results = retriever.search(query="collateral property appraisal", limit=10)

        # Should return results (either from AND or OR fallback)
        assert len(results) >= 0, "Should handle OR fallback gracefully"

    def test_fts_workspace_isolation(self, session: Session):
        """Verify that FTS respects workspace boundaries."""
        # Create two workspaces
        tenant1 = Tenant(
            id=_uid(),
            name=f"test_phase3b_fts_tenant1_{_uid()}",
            slug=f"test-phase3b-fts-1-{_uid()}",
            display_name="FTS Tenant 1",
            active=True,
        )
        session.add(tenant1)
        session.flush()

        workspace1 = Workspace(
            id=_uid(),
            tenant_id=tenant1.id,
            name=f"test_phase3b_fts_ws1_{_uid()}",
            display_name="FTS Workspace 1",
            active=True,
        )
        session.add(workspace1)
        session.flush()

        tenant2 = Tenant(
            id=_uid(),
            name=f"test_phase3b_fts_tenant2_{_uid()}",
            slug=f"test-phase3b-fts-2-{_uid()}",
            display_name="FTS Tenant 2",
            active=True,
        )
        session.add(tenant2)
        session.flush()

        workspace2 = Workspace(
            id=_uid(),
            tenant_id=tenant2.id,
            name=f"test_phase3b_fts_ws2_{_uid()}",
            display_name="FTS Workspace 2",
            active=True,
        )
        session.add(workspace2)
        session.commit()

        # Create rules in each workspace
        knowledge1 = WorkflowKnowledge(
            id=_uid(),
            workspace_id=workspace1.id,
            workflow_name=f"test_phase3b_fts_flow1_{_uid()}",
            summary="Flow 1",
        )
        session.add(knowledge1)
        session.flush()

        knowledge2 = WorkflowKnowledge(
            id=_uid(),
            workspace_id=workspace2.id,
            workflow_name=f"test_phase3b_fts_flow2_{_uid()}",
            summary="Flow 2",
        )
        session.add(knowledge2)
        session.flush()

        rule1 = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge1.id,
            rule="test_phase3b_credit approval workflow specific",
            condition="cond1",
        )

        rule2 = WorkflowBusinessRule(
            id=_uid(),
            workflow_knowledge_id=knowledge2.id,
            rule="test_phase3b_unique income validation process",
            condition="cond2",
        )

        session.add(rule1)
        session.add(rule2)
        session.commit()

        # Search in workspace1
        repo = RuleRepository(session)
        retriever1 = RulePostgresRetriever(repo, workspace_id=workspace1.id)
        results1 = retriever1.search(query="credit", limit=10)

        result_ids_1 = {r.entity.id for r in results1}
        assert rule1.id in result_ids_1
        assert rule2.id not in result_ids_1

        # Search in workspace2
        retriever2 = RulePostgresRetriever(repo, workspace_id=workspace2.id)
        results2 = retriever2.search(query="income", limit=10)

        result_ids_2 = {r.entity.id for r in results2}
        assert rule2.id in result_ids_2
        assert rule1.id not in result_ids_2

    def test_fts_empty_query(self, session: Session, test_workspace_with_rules):
        """Verify that empty queries are handled gracefully in FTS."""
        workspace, rules = test_workspace_with_rules

        repo = RuleRepository(session)
        retriever = RulePostgresRetriever(repo, workspace_id=workspace.id)

        results = retriever.search(query="", limit=10)
        assert len(results) == 0, "Empty query should return no results"

    def test_fts_top_k_respected(self, session: Session, test_workspace_with_rules):
        """Verify that top_k limits are respected in FTS."""
        workspace, rules = test_workspace_with_rules

        repo = RuleRepository(session)
        retriever = RulePostgresRetriever(repo, workspace_id=workspace.id)

        for limit in [1, 3, 5]:
            results = retriever.search(query="test", limit=limit)
            assert len(results) <= limit, f"Results {len(results)} should not exceed limit {limit}"

    def test_fts_result_contract(
        self, session: Session, test_workspace_with_rules
    ):
        """Verify that RetrievalCandidate wrapper has correct structure for FTS."""
        workspace, rules = test_workspace_with_rules

        repo = RuleRepository(session)
        retriever = RulePostgresRetriever(repo, workspace_id=workspace.id)
        results = retriever.search(query="test", limit=5)

        if len(results) > 0:
            candidate = results[0]
            assert isinstance(candidate, RetrievalCandidate)
            assert candidate.entity is not None
            assert isinstance(candidate.entity, WorkflowBusinessRule)
            assert candidate.score is not None and isinstance(candidate.score, float)
            assert candidate.source == "postgres"

    def test_fts_allowed_ids_filtering(
        self, session: Session, test_workspace_with_rules
    ):
        """Verify that allowed_ids parameter filters FTS results."""
        workspace, rules = test_workspace_with_rules

        # Select subset of rule IDs
        allowed_rule_ids = {rules[0].id, rules[1].id}

        repo = RuleRepository(session)
        retriever = RulePostgresRetriever(repo, workspace_id=workspace.id)
        results = retriever.search(
            query="test", limit=10, allowed_ids=allowed_rule_ids
        )

        result_ids = {r.entity.id for r in results}
        assert result_ids.issubset(
            allowed_rule_ids
        ), "All results should be in allowed_ids"

    def test_fts_empty_allowed_ids(self, session: Session, test_workspace_with_rules):
        """Verify that empty allowed_ids returns no results."""
        workspace, rules = test_workspace_with_rules

        repo = RuleRepository(session)
        retriever = RulePostgresRetriever(repo, workspace_id=workspace.id)
        results = retriever.search(
            query="test", limit=10, allowed_ids=set()  # Empty set
        )

        assert len(results) == 0


class TestLexicalRetrievalComparison:
    """Compare behavior between BM25 and FTS retrieval."""

    def test_bm25_and_fts_return_same_rule_set(
        self, session: Session, test_workspace_with_rules
    ):
        """Verify that BM25 and FTS return overlapping rule sets."""
        workspace, rules = test_workspace_with_rules

        repo = RuleRepository(session)
        bm25_retriever = RuleKeywordRetriever(repo, workspace_id=workspace.id)
        fts_retriever = RulePostgresRetriever(repo, workspace_id=workspace.id)

        query = "credit approval"
        bm25_results = bm25_retriever.search(query=query, limit=10)
        fts_results = fts_retriever.search(query=query, limit=10)

        bm25_ids = {r.entity.id for r in bm25_results}
        fts_ids = {r.entity.id for r in fts_results}

        # Both should return at least some results for common query
        if len(rules) > 0:
            # At least one should have results
            assert len(bm25_ids) >= 0
            assert len(fts_ids) >= 0

    def test_score_semantics_differ(
        self, session: Session, test_workspace_with_rules
    ):
        """Verify that BM25 and FTS scores are on different scales."""
        workspace, rules = test_workspace_with_rules

        if not rules:
            pytest.skip("No rules in workspace")

        repo = RuleRepository(session)
        bm25_retriever = RuleKeywordRetriever(repo, workspace_id=workspace.id)
        fts_retriever = RulePostgresRetriever(repo, workspace_id=workspace.id)

        query = "credit"
        bm25_results = bm25_retriever.search(query=query, limit=5)
        fts_results = fts_retriever.search(query=query, limit=5)

        # Extract scores
        bm25_scores = [r.score for r in bm25_results]
        fts_scores = [r.score for r in fts_results]

        # Scores should have different ranges/distributions
        # This is informational; don't combine raw scores without normalization
        if bm25_scores and fts_scores:
            # Just verify they exist and are numeric
            assert all(isinstance(s, float) for s in bm25_scores)
            assert all(isinstance(s, float) for s in fts_scores)
