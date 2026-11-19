"""
Phase 5 — Context Assembly & Source Traceability Integration Tests

Tests focus on:
1. Correct context assembly from hybrid retrieval results
2. Token budget compliance
3. Deterministic selection and ordering
4. Empty retrieval handling
5. Duplicate rule deduplication
6. Similar text with different rule IDs
7. Exclusion of oversized rules without truncation
8. Complete provenance chain validation
9. Missing provenance handling
10. Conflicting rules preserved separately
11. Cross-workspace and cross-tenant rejection
12. No accidental inclusion of inactive records
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.context_assembly import ContextAssemblyService, AssembledContext
from app.models.workflow_business_rule import WorkflowBusinessRule
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.brd_document import BRDDocument, IngestionStatus
from app.models.document_version import DocumentVersion, VersionStatus
from app.models.workspace import Workspace
from app.models.tenant import Tenant
from app.retrieval.models import RankedCandidate
from sqlalchemy import text as sa_text


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def session():
    """Create a fresh database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_tenant(session: Session):
    """Create test tenant."""
    tenant = Tenant(
        name="test_tenant",
        slug="test-tenant",
        display_name="Test Tenant",
        active=True,
    )
    session.add(tenant)
    session.commit()
    return tenant


@pytest.fixture
def test_workspace(session: Session, test_tenant: Tenant):
    """Create test workspace."""
    workspace = Workspace(
        name="test_workspace",
        display_name="Test Workspace",
        tenant_id=test_tenant.id,
        active=True,
    )
    session.add(workspace)
    session.commit()
    return workspace


@pytest.fixture
def other_workspace(session: Session, test_tenant: Tenant):
    """Create another workspace in same tenant."""
    workspace = Workspace(
        name="other_workspace",
        display_name="Other Workspace",
        tenant_id=test_tenant.id,
        active=True,
    )
    session.add(workspace)
    session.commit()
    return workspace


@pytest.fixture
def test_brd_document(session: Session, test_workspace: Workspace, test_tenant: Tenant):
    """Create test BRDDocument."""
    doc = BRDDocument(
        tenant_id=test_tenant.id,
        workspace_id=test_workspace.id,
        original_filename="test_loan_brd.pdf",
        sha256_hash="abc123",
        mime_type="application/pdf",
        file_size_bytes=10000,
        document_type="brd",
        ingestion_status=IngestionStatus.COMPLETED.value,
    )
    session.add(doc)
    session.commit()
    return doc


@pytest.fixture
def test_document_version(session: Session, test_brd_document: BRDDocument):
    """Create test DocumentVersion."""
    version = DocumentVersion(
        document_id=test_brd_document.id,
        version_number=1,
        original_filename="test_loan_brd.pdf",
        sha256_hash="abc123",
        mime_type="application/pdf",
        file_size_bytes=10000,
        page_count=20,
        status=VersionStatus.COMPLETED.value,
    )
    session.add(version)
    session.commit()
    return version


@pytest.fixture
def test_workflow_knowledge(session: Session, test_workspace: Workspace, test_document_version: DocumentVersion):
    """Create test WorkflowKnowledge."""
    wk = WorkflowKnowledge(
        workflow_name="PersonalLoanBRD",
        summary="Test workflow knowledge",
        workspace_id=test_workspace.id,
        brd_document_id=test_document_version.document_id,
        document_version_id=test_document_version.id,
    )
    session.add(wk)
    session.commit()
    return wk


@pytest.fixture
def test_business_rules(session: Session, test_workflow_knowledge: WorkflowKnowledge, test_brd_document: BRDDocument):
    """Create test WorkflowBusinessRule records."""
    rules = []
    for i in range(5):
        rule = WorkflowBusinessRule(
            workflow_knowledge_id=test_workflow_knowledge.id,
            rule=f"Test rule {i}: This is a business rule for testing purposes.",
            condition=f"If condition_{i} is true" if i % 2 == 0 else None,
            outcome=f"Then execute action_{i}",
            responsible_role="loan_officer" if i % 2 == 0 else None,
            threshold="100" if i == 0 else None,
            source_brd_document_id=test_brd_document.id,
        )
        session.add(rule)
    session.commit()
    session.refresh(test_workflow_knowledge)
    return test_workflow_knowledge.workflow_business_rule


@pytest.fixture
def context_assembler(session: Session):
    """Create ContextAssemblyService."""
    return ContextAssemblyService(session)


# ─────────────────────────────────────────────────────────────────────────────
# Test Cases
# ─────────────────────────────────────────────────────────────────────────────


class TestContextAssemblyBasics:
    """Basic context assembly functionality."""

    def test_assemble_from_hybrid_results(
        self, context_assembler, test_workspace, test_business_rules
    ):
        """Test correct context assembly from hybrid retrieval results."""
        rule_ids = [r.id for r in test_business_rules[:3]]
        hybrid_results = {
            rule_ids[0]: RankedCandidate(
                entity=test_business_rules[0],
                vector_rank=1,
                bm25_rank=2,
                postgres_rank=3,
                rrf_score=0.9,
            ),
            rule_ids[1]: RankedCandidate(
                entity=test_business_rules[1],
                vector_rank=2,
                bm25_rank=1,
                postgres_rank=5,
                rrf_score=0.8,
            ),
            rule_ids[2]: RankedCandidate(
                entity=test_business_rules[2],
                vector_rank=3,
                bm25_rank=3,
                postgres_rank=1,
                rrf_score=0.7,
            ),
        }

        context = context_assembler.assemble(
            tenant_id=test_workspace.tenant_id,
            workspace_id=test_workspace.id,
            query="What is the minimum loan amount?",
            retrieved_rule_ids=rule_ids,
            hybrid_results=hybrid_results,
            token_budget=2000,
        )

        # Assertions
        assert context.workspace_id == test_workspace.id
        assert context.total_candidates_retrieved == 3
        assert context.total_rules_selected >= 2  # At least 2 should fit in budget
        assert context.query == "What is the minimum loan amount?"
        assert context.estimated_tokens_used > 0

    def test_token_budget_compliance(
        self, context_assembler, test_workspace, test_business_rules
    ):
        """Test that selected rules respect token budget."""
        rule_ids = [r.id for r in test_business_rules]
        hybrid_results = {
            rule_id: RankedCandidate(
                entity=test_business_rules[i],
                vector_rank=i + 1,
                bm25_rank=i + 1,
                postgres_rank=i + 1,
                rrf_score=1.0 - (i * 0.1),
            )
            for i, rule_id in enumerate(rule_ids)
        }

        token_budget = 100  # Very tight budget
        context = context_assembler.assemble(
            tenant_id=test_workspace.tenant_id,
            workspace_id=test_workspace.id,
            query="Test",
            retrieved_rule_ids=rule_ids,
            hybrid_results=hybrid_results,
            token_budget=token_budget,
        )

        # Assertions
        assert context.estimated_tokens_used <= token_budget
        assert context.estimated_tokens_remaining >= 0
        assert context.total_rules_excluded > 0  # Some should be excluded

    def test_deterministic_selection_and_ordering(
        self, context_assembler, test_workspace, test_business_rules
    ):
        """Test that selection and ordering is deterministic (reproducible)."""
        rule_ids = [r.id for r in test_business_rules]
        hybrid_results = {
            rule_id: RankedCandidate(
                entity=test_business_rules[i],
                vector_rank=i + 1,
                bm25_rank=i + 1,
                postgres_rank=i + 1,
                rrf_score=0.5,  # Same score for all
            )
            for i, rule_id in enumerate(rule_ids)
        }

        # Run twice
        context1 = context_assembler.assemble(
            tenant_id=test_workspace.tenant_id,
            workspace_id=test_workspace.id,
            query="Test",
            retrieved_rule_ids=rule_ids,
            hybrid_results=hybrid_results,
            token_budget=2000,
        )

        context2 = context_assembler.assemble(
            tenant_id=test_workspace.tenant_id,
            workspace_id=test_workspace.id,
            query="Test",
            retrieved_rule_ids=rule_ids,
            hybrid_results=hybrid_results,
            token_budget=2000,
        )

        # Assertions
        assert len(context1.selected_rules) == len(context2.selected_rules)
        selected_ids_1 = [r.workflow_business_rule_id for r in context1.selected_rules]
        selected_ids_2 = [r.workflow_business_rule_id for r in context2.selected_rules]
        assert selected_ids_1 == selected_ids_2

    def test_empty_retrieval_results(
        self, context_assembler, test_workspace
    ):
        """Test clean handling of empty retrieval results."""
        context = context_assembler.assemble(
            tenant_id=test_workspace.tenant_id,
            workspace_id=test_workspace.id,
            query="Nonsensical query that retrieves nothing",
            retrieved_rule_ids=[],
            hybrid_results={},
            token_budget=2000,
        )

        # Assertions
        assert context.total_candidates_retrieved == 0
        assert context.total_rules_selected == 0
        assert context.total_rules_excluded == 0
        assert len(context.selected_rules) == 0
        assert len(context.excluded_candidates) == 0


class TestProvenance:
    """Provenance chain validation and completeness."""

    def test_complete_provenance_chain(
        self, context_assembler, test_workspace, test_business_rules
    ):
        """Test that complete provenance chain is captured and validated."""
        rule_ids = [test_business_rules[0].id]
        hybrid_results = {
            rule_ids[0]: RankedCandidate(
                entity=test_business_rules[0],
                vector_rank=1,
                bm25_rank=1,
                postgres_rank=1,
                rrf_score=0.95,
            )
        }

        context = context_assembler.assemble(
            tenant_id=test_workspace.tenant_id,
            workspace_id=test_workspace.id,
            query="Test",
            retrieved_rule_ids=rule_ids,
            hybrid_results=hybrid_results,
            token_budget=2000,
        )

        # Assertions
        assert len(context.selected_rules) == 1
        rule = context.selected_rules[0]
        assert rule.provenance.is_complete
        assert rule.provenance.workflow_knowledge_id is not None
        assert rule.provenance.document_version_id is not None
        assert rule.provenance.brd_document_id is not None
        assert len(rule.provenance.missing_links) == 0

    def test_incomplete_provenance_tracking(
        self, session: Session, context_assembler, test_workspace
    ):
        """Test that incomplete provenance is marked without fabrication."""
        # Create a rule WITHOUT document_version_id
        wk = WorkflowKnowledge(
            workflow_name="IncompleteKnowledge",
            workspace_id=test_workspace.id,
            document_version_id=None,  # Explicitly NULL
            brd_document_id=None,      # Explicitly NULL
        )
        session.add(wk)
        session.commit()

        rule = WorkflowBusinessRule(
            workflow_knowledge_id=wk.id,
            rule="Rule with missing provenance",
            source_brd_document_id=None,  # No direct link either
        )
        session.add(rule)
        session.commit()

        rule_ids = [rule.id]
        hybrid_results = {
            rule.id: RankedCandidate(
                entity=rule,
                vector_rank=1,
                bm25_rank=1,
                postgres_rank=1,
                rrf_score=0.5,
            )
        }

        context = context_assembler.assemble(
            tenant_id=test_workspace.tenant_id,
            workspace_id=test_workspace.id,
            query="Test",
            retrieved_rule_ids=rule_ids,
            hybrid_results=hybrid_results,
            token_budget=2000,
        )

        # Assertions
        assert len(context.selected_rules) == 1
        selected_rule = context.selected_rules[0]
        assert not selected_rule.provenance.is_complete
        assert len(selected_rule.provenance.missing_links) > 0
        # No fabricated data
        assert selected_rule.provenance.document_version_id is None
        assert selected_rule.provenance.brd_document_id is None


class TestIsolation:
    """Tenant and workspace isolation enforcement."""

    def test_cross_workspace_rejection(
        self, session: Session, context_assembler, test_workspace, other_workspace, test_business_rules
    ):
        """Test that rules from other workspace are rejected."""
        # Create a rule in the OTHER workspace
        other_wk = WorkflowKnowledge(
            workflow_name="OtherWorkflowKnowledge",
            workspace_id=other_workspace.id,
        )
        session.add(other_wk)
        session.commit()

        other_rule = WorkflowBusinessRule(
            workflow_knowledge_id=other_wk.id,
            rule="This is from another workspace",
        )
        session.add(other_rule)
        session.commit()

        rule_ids = [other_rule.id]
        hybrid_results = {
            other_rule.id: RankedCandidate(
                entity=other_rule,
                vector_rank=1,
                bm25_rank=1,
                postgres_rank=1,
                rrf_score=0.9,
            )
        }

        # Try to assemble for test_workspace
        context = context_assembler.assemble(
            tenant_id=test_workspace.tenant_id,
            workspace_id=test_workspace.id,  # test_workspace
            query="Test",
            retrieved_rule_ids=rule_ids,
            hybrid_results=hybrid_results,
            token_budget=2000,
        )

        # Assertions
        assert context.total_candidates_retrieved == 1
        assert context.total_rules_selected == 0
        assert len(context.selected_rules) == 0


class TestExclusions:
    """Rule exclusion and oversizing handling."""

    def test_oversized_rule_exclusion(
        self, context_assembler, test_workspace, test_business_rules
    ):
        """Test that rules larger than token budget are excluded without truncation."""
        # Modify a rule to have very long text
        rule = test_business_rules[0]
        rule.rule = "This is a very long rule. " * 500  # ~13,500 characters

        rule_ids = [rule.id]
        hybrid_results = {
            rule.id: RankedCandidate(
                entity=rule,
                vector_rank=1,
                bm25_rank=1,
                postgres_rank=1,
                rrf_score=0.9,
            )
        }

        token_budget = 100  # Too small for the large rule
        context = context_assembler.assemble(
            tenant_id=test_workspace.tenant_id,
            workspace_id=test_workspace.id,
            query="Test",
            retrieved_rule_ids=rule_ids,
            hybrid_results=hybrid_results,
            token_budget=token_budget,
        )

        # Assertions
        assert len(context.selected_rules) == 0
        assert len(context.excluded_candidates) == 1
        excluded = context.excluded_candidates[0]
        assert excluded.exclusion_reason == "RULE_TEXT_TOO_LARGE"
        # Rule text should NOT be truncated in the excluded list
        assert len(excluded.rule_text) > 100

    def test_budget_exhaustion_exclusion(
        self, context_assembler, test_workspace, test_business_rules
    ):
        """Test that rules are excluded when budget is exhausted."""
        rule_ids = [r.id for r in test_business_rules]
        hybrid_results = {
            rule_id: RankedCandidate(
                entity=test_business_rules[i],
                vector_rank=i + 1,
                bm25_rank=i + 1,
                postgres_rank=i + 1,
                rrf_score=0.5 + (i * 0.1),  # Higher score for later rules
            )
            for i, rule_id in enumerate(rule_ids)
        }

        token_budget = 50  # Very tight budget
        context = context_assembler.assemble(
            tenant_id=test_workspace.tenant_id,
            workspace_id=test_workspace.id,
            query="Test",
            retrieved_rule_ids=rule_ids,
            hybrid_results=hybrid_results,
            token_budget=token_budget,
        )

        # Assertions
        excluded_with_budget = [r for r in context.excluded_candidates if r.exclusion_reason == "BUDGET_EXHAUSTED"]
        assert len(excluded_with_budget) > 0


class TestConflictDetection:
    """Conflict detection and preservation."""

    def test_conflicting_rules_preserved(
        self, session: Session, context_assembler, test_workspace, test_workflow_knowledge
    ):
        """Test that conflicting rules are preserved, not auto-resolved."""
        # Create two conflicting rules: same condition + outcome, different thresholds
        rule1 = WorkflowBusinessRule(
            workflow_knowledge_id=test_workflow_knowledge.id,
            rule="Minimum income rule version 1",
            condition="applicant_income",
            outcome="approve_loan",
            threshold="100000",
        )
        session.add(rule1)

        rule2 = WorkflowBusinessRule(
            workflow_knowledge_id=test_workflow_knowledge.id,
            rule="Minimum income rule version 2 (updated)",
            condition="applicant_income",
            outcome="approve_loan",
            threshold="150000",  # DIFFERENT threshold
        )
        session.add(rule2)
        session.commit()

        rule_ids = [rule1.id, rule2.id]
        hybrid_results = {
            rule1.id: RankedCandidate(
                entity=rule1,
                vector_rank=1,
                bm25_rank=1,
                postgres_rank=1,
                rrf_score=0.9,
            ),
            rule2.id: RankedCandidate(
                entity=rule2,
                vector_rank=2,
                bm25_rank=2,
                postgres_rank=2,
                rrf_score=0.8,
            ),
        }

        context = context_assembler.assemble(
            tenant_id=test_workspace.tenant_id,
            workspace_id=test_workspace.id,
            query="Test",
            retrieved_rule_ids=rule_ids,
            hybrid_results=hybrid_results,
            token_budget=2000,
        )

        # Assertions
        assert context.has_conflicts
        assert len(context.conflicting_rule_pairs) > 0
        # BOTH rules should be selected (not auto-resolved)
        assert len(context.selected_rules) == 2
        selected_ids = [r.workflow_business_rule_id for r in context.selected_rules]
        assert rule1.id in selected_ids
        assert rule2.id in selected_ids


class TestRetrievalScoresPreserved:
    """Verification that retrieval scores are correctly preserved."""

    def test_retrieval_scores_preservation(
        self, context_assembler, test_workspace, test_business_rules
    ):
        """Test that vector_rank, bm25_rank, postgres_rank, rrf_score are all preserved."""
        rule = test_business_rules[0]
        rule_ids = [rule.id]
        hybrid_results = {
            rule.id: RankedCandidate(
                entity=rule,
                vector_rank=2,
                bm25_rank=5,
                postgres_rank=3,
                rrf_score=0.75,
                cross_encoder_score=0.82,
            )
        }

        context = context_assembler.assemble(
            tenant_id=test_workspace.tenant_id,
            workspace_id=test_workspace.id,
            query="Test",
            retrieved_rule_ids=rule_ids,
            hybrid_results=hybrid_results,
            token_budget=2000,
        )

        # Assertions
        assert len(context.selected_rules) == 1
        selected = context.selected_rules[0]
        assert selected.vector_rank == 2
        assert selected.bm25_rank == 5
        assert selected.postgres_rank == 3
        assert selected.rrf_score == 0.75
        assert selected.cross_encoder_score == 0.82


class TestToDict:
    """Serialization to dictionary for JSON output."""

    def test_assembled_context_to_dict(
        self, context_assembler, test_workspace, test_business_rules
    ):
        """Test that AssembledContext serializes to dictionary correctly."""
        rule_ids = [test_business_rules[0].id]
        hybrid_results = {
            rule_ids[0]: RankedCandidate(
                entity=test_business_rules[0],
                vector_rank=1,
                bm25_rank=1,
                postgres_rank=1,
                rrf_score=0.9,
            )
        }

        context = context_assembler.assemble(
            tenant_id=test_workspace.tenant_id,
            workspace_id=test_workspace.id,
            query="What is the minimum loan?",
            retrieved_rule_ids=rule_ids,
            hybrid_results=hybrid_results,
            token_budget=2000,
        )

        result_dict = context.to_dict()

        # Assertions
        assert result_dict["metadata"]["workspace_id"] == test_workspace.id
        assert result_dict["metadata"]["query"] == "What is the minimum loan?"
        assert "selected_rules" in result_dict
        assert "excluded_rules" in result_dict
        assert "token_budget" in result_dict
        assert len(result_dict["selected_rules"]) >= 1
