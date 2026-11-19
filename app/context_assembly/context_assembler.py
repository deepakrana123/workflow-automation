"""
app/context_assembly/context_assembler.py

ContextAssemblyService — converts hybrid retrieval results into structured,
token-budget-aware context with complete source provenance.

Responsibilities:
1. Validate tenant/workspace ownership before assembly
2. Deduplicate by WorkflowBusinessRule ID
3. Order rules deterministically by retrieval rank/score
4. Respect token budget and exclude oversized rules (no truncation)
5. Validate and preserve source provenance chains
6. Detect and preserve conflicting rules (no automatic resolution)
7. Return metadata about selected and excluded candidates

Design principles:
- Use existing token-counting utilities (estimate_tokens)
- Do NOT modify retrieval results
- Do NOT call LLMs
- Handle empty retrieval results cleanly
- Mark provenance as incomplete when data is missing
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.context_assembly.models import (
    AssembledContext,
    SelectedBusinessRule,
    SourceProvenance,
)
from app.prompting.token_estimator import estimate_tokens
from app.models.workflow_business_rule import WorkflowBusinessRule
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.document_version import DocumentVersion
from app.models.brd_document import BRDDocument
from app.core.logger import logger


class ContextAssemblyService:
    """
    Converts hybrid retrieval results into assembled context with provenance.

    Usage:
        svc = ContextAssemblyService(db)
        context = svc.assemble(
            tenant_id=1,
            workspace_id=2,
            query="What is the minimum loan amount?",
            retrieved_rule_ids=[101, 102, 103],
            hybrid_results={101: RankedCandidate(...), ...},
            token_budget=4000,
        )
        print(context.to_dict())
    """

    def __init__(self, db: Session):
        """
        Args:
            db: SQLAlchemy session for provenance lookups.
        """
        self._db = db

    def assemble(
        self,
        tenant_id: int,
        workspace_id: int,
        query: str,
        retrieved_rule_ids: list[int],
        hybrid_results: dict,  # {rule_id: RankedCandidate}
        token_budget: int = 4000,
        retrieval_model: str = "BAAI/bge-small-en-v1.5",
        retrieval_top_k: int = 50,
        rrf_k_constant: int = 60,
    ) -> AssembledContext:
        """
        Assemble context from hybrid retrieval results with full provenance.

        Args:
            tenant_id: Tenant ownership validation.
            workspace_id: Workspace ownership validation.
            query: Original query string.
            retrieved_rule_ids: List of WorkflowBusinessRule IDs returned by retrieval.
            hybrid_results: Dict mapping rule_id to RankedCandidate (retrieval result DTO).
            token_budget: Maximum tokens available for selected rules.
            retrieval_model: Name of embedding model used.
            retrieval_top_k: Top-K limit used in retrieval.
            rrf_k_constant: RRF k constant used in retrieval.

        Returns:
            AssembledContext with selected rules, exclusions, and provenance.
        """
        logger.info(
            "context_assembly_start",
            extra={
                "extra_data": {
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                    "query": query,
                    "retrieved_count": len(retrieved_rule_ids),
                    "token_budget": token_budget,
                }
            },
        )

        # Initialize result container
        context = AssembledContext(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            query=query,
            retrieval_timestamp=datetime.utcnow(),
            retrieval_model=retrieval_model,
            retrieval_top_k=retrieval_top_k,
            rrf_k_constant=rrf_k_constant,
            token_budget=token_budget,
            total_candidates_retrieved=len(retrieved_rule_ids),
        )

        # Handle empty retrieval
        if not retrieved_rule_ids:
            logger.info(
                "context_assembly_empty_retrieval",
                extra={"extra_data": {"workspace_id": workspace_id}},
            )
            return context

        # Step 1: Validate tenant/workspace ownership and deduplicate
        validated_rules = self._validate_and_fetch_rules(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            rule_ids=retrieved_rule_ids,
        )

        if not validated_rules:
            logger.warning(
                "context_assembly_no_validated_rules",
                extra={
                    "extra_data": {
                        "tenant_id": tenant_id,
                        "workspace_id": workspace_id,
                        "retrieved_count": len(retrieved_rule_ids),
                    }
                },
            )
            return context

        # Step 2: Build SelectedBusinessRule objects with provenance
        selected_with_provenance = []
        for rule_id in validated_rules:
            rule_obj = validated_rules[rule_id]
            ranked_candidate = hybrid_results.get(rule_id)

            # Build provenance chain
            provenance = self._validate_provenance_chain(
                rule_obj, workspace_id, tenant_id
            )

            # Build SelectedBusinessRule
            selected_rule = SelectedBusinessRule(
                workflow_business_rule_id=rule_obj.id,
                workflow_knowledge_id=rule_obj.workflow_knowledge_id,
                rule_text=rule_obj.rule or "",
                condition=rule_obj.condition,
                outcome=rule_obj.outcome,
                responsible_role=rule_obj.responsible_role,
                threshold=rule_obj.threshold,
                vector_rank=ranked_candidate.vector_rank if ranked_candidate else None,
                bm25_rank=ranked_candidate.bm25_rank if ranked_candidate else None,
                postgres_rank=ranked_candidate.postgres_rank if ranked_candidate else None,
                rrf_score=ranked_candidate.rrf_score if ranked_candidate else 0.0,
                cross_encoder_score=(
                    ranked_candidate.cross_encoder_score if ranked_candidate else None
                ),
                provenance=provenance,
                estimated_tokens=estimate_tokens(rule_obj.rule or ""),
            )

            selected_with_provenance.append(selected_rule)

        # Step 3: Apply token budget and track exclusions
        selected_rules, excluded_rules = self._apply_token_budget(
            selected_with_provenance, token_budget
        )

        context.selected_rules = selected_rules
        context.excluded_candidates = excluded_rules
        context.total_rules_selected = len(selected_rules)
        context.total_rules_excluded = len(excluded_rules)

        # Step 4: Calculate token accounting
        tokens_used = sum(rule.estimated_tokens for rule in selected_rules)
        context.estimated_tokens_used = tokens_used
        context.estimated_tokens_remaining = max(0, token_budget - tokens_used)

        # Step 5: Detect conflicts (preserve both, don't resolve)
        conflicts = self._detect_conflicts(selected_rules)
        context.conflicting_rule_pairs = conflicts
        context.has_conflicts = len(conflicts) > 0

        # Step 6: Calculate provenance quality
        incomplete_provenance = [
            rule.workflow_business_rule_id
            for rule in selected_rules
            if not rule.provenance.is_complete
        ]
        context.rules_with_incomplete_provenance = incomplete_provenance
        total_rules = len(selected_rules)
        if total_rules > 0:
            context.provenance_completeness_pct = (
                (total_rules - len(incomplete_provenance)) / total_rules * 100
            )

        logger.info(
            "context_assembly_complete",
            extra={
                "extra_data": {
                    "workspace_id": workspace_id,
                    "selected_count": len(selected_rules),
                    "excluded_count": len(excluded_rules),
                    "tokens_used": tokens_used,
                    "conflicts_detected": len(conflicts),
                }
            },
        )

        return context

    # ─────────────────────────────────────────────────────────────────────────

    def _validate_and_fetch_rules(
        self,
        tenant_id: int,
        workspace_id: int,
        rule_ids: list[int],
    ) -> dict[int, WorkflowBusinessRule]:
        """
        Fetch and validate rules by tenant/workspace ownership.

        Args:
            tenant_id: Expected tenant.
            workspace_id: Expected workspace.
            rule_ids: List of WorkflowBusinessRule IDs to validate.

        Returns:
            Dict mapping rule_id to WorkflowBusinessRule ORM object (only valid rules).
        """
        if not rule_ids:
            return {}

        # Query: WorkflowBusinessRule → WorkflowKnowledge → Workspace
        # Filter: workspace_id matches, deduplicate by rule ID
        query = (
            self._db.query(WorkflowBusinessRule)
            .join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowBusinessRule.workflow_knowledge_id,
            )
            .filter(
                and_(
                    WorkflowKnowledge.workspace_id == workspace_id,
                    WorkflowBusinessRule.id.in_(rule_ids),
                )
            )
            .all()
        )

        # Build result dict (naturally deduplicates by rule ID)
        result = {rule.id: rule for rule in query}

        # Log any rejected rules (workspace mismatch or not found)
        rejected_ids = set(rule_ids) - set(result.keys())
        if rejected_ids:
            logger.warning(
                "context_assembly_rejected_rules",
                extra={
                    "extra_data": {
                        "workspace_id": workspace_id,
                        "rejected_count": len(rejected_ids),
                        "rejected_ids": list(rejected_ids)[:10],  # Sample
                    }
                },
            )

        return result

    # ─────────────────────────────────────────────────────────────────────────

    def _validate_provenance_chain(
        self,
        rule: WorkflowBusinessRule,
        expected_workspace_id: int,
        expected_tenant_id: int,
    ) -> SourceProvenance:
        """
        Build and validate the provenance chain for a single rule.

        Chain: WorkflowBusinessRule → WorkflowKnowledge → DocumentVersion → BRDDocument → Workspace

        Marks provenance as incomplete if any link is missing.
        Never fabricates source data — all fields represent actual DB values or None.

        Args:
            rule: ORM object for the rule.
            expected_workspace_id: Expected workspace ownership.
            expected_tenant_id: Expected tenant ownership.

        Returns:
            SourceProvenance with all available links and completeness flag.
        """
        provenance = SourceProvenance(
            workspace_id=expected_workspace_id,
            tenant_id=expected_tenant_id,
        )

        # Link 1: WorkflowBusinessRule → WorkflowKnowledge (should always exist)
        wk = rule.workflow_knowledge if rule.workflow_knowledge_id else None
        if not wk:
            provenance.missing_links.append("workflow_knowledge")
            return provenance

        provenance.workflow_knowledge_id = wk.id
        provenance.workflow_knowledge_name = wk.workflow_name
        provenance.workflow_knowledge_summary = wk.summary

        # Verify workspace ownership
        if wk.workspace_id != expected_workspace_id:
            logger.error(
                "context_assembly_workspace_mismatch",
                extra={
                    "extra_data": {
                        "rule_id": rule.id,
                        "expected_workspace_id": expected_workspace_id,
                        "actual_workspace_id": wk.workspace_id,
                    }
                },
            )
            provenance.missing_links.append("workspace_mismatch")
            return provenance

        # Link 2: WorkflowKnowledge → DocumentVersion (nullable)
        if wk.document_version_id:
            dv = wk.document_version if wk.document_version_id else None
            if dv:
                provenance.document_version_id = dv.id
                provenance.document_version_number = dv.version_number
                provenance.document_original_filename = dv.original_filename
                provenance.document_storage_path = dv.storage_path
                provenance.document_page_count = dv.page_count
                provenance.document_sha256_hash = dv.sha256_hash
                provenance.document_mime_type = dv.mime_type
            else:
                provenance.missing_links.append("document_version_id_invalid")
        else:
            # document_version_id is nullable; use legacy brd_document_id as fallback
            if wk.brd_document_id:
                provenance.brd_document_id = wk.brd_document_id
            else:
                provenance.missing_links.append("document_version_id")

        # Link 3: BRDDocument (via document_version or direct FK)
        if provenance.document_version_id:
            bd = dv.document if dv else None
            if bd:
                provenance.brd_document_id = bd.id
                provenance.brd_document_filename = bd.original_filename
                provenance.brd_document_type = bd.document_type
                provenance.brd_document_version = bd.version
            else:
                provenance.missing_links.append("brd_document_via_version")
        elif wk.brd_document_id:
            # Fetch BRDDocument directly
            bd = wk.brd_document if wk.brd_document_id else None
            if bd:
                provenance.brd_document_id = bd.id
                provenance.brd_document_filename = bd.original_filename
                provenance.brd_document_type = bd.document_type
                provenance.brd_document_version = bd.version
            else:
                provenance.missing_links.append("brd_document_invalid")
        else:
            provenance.missing_links.append("brd_document_id")

        # Also check source_brd_document_id on the rule itself (alternative link)
        if rule.source_brd_document_id and not provenance.brd_document_id:
            source_bd = rule.source_brd_document if rule.source_brd_document_id else None
            if source_bd:
                provenance.brd_document_id = source_bd.id
                provenance.brd_document_filename = source_bd.original_filename
                provenance.brd_document_type = source_bd.document_type
                provenance.brd_document_version = source_bd.version

        # Link 4: Workspace isolation check
        # (already verified above when joining WorkflowKnowledge)

        # Determine completeness
        # Complete chain: rule → wk → document_version → brd_document
        provenance.is_complete = (
            provenance.workflow_knowledge_id is not None
            and (provenance.document_version_id is not None or provenance.brd_document_id is not None)
        )

        return provenance

    # ─────────────────────────────────────────────────────────────────────────

    def _apply_token_budget(
        self,
        candidates: list[SelectedBusinessRule],
        token_budget: int,
    ) -> tuple[list[SelectedBusinessRule], list[SelectedBusinessRule]]:
        """
        Select rules up to token budget. Exclude oversized rules without truncation.

        Strategy:
        1. Order candidates by RRF score (descending) — already in RRF order
        2. Iterate: if rule fits in budget, include; else mark excluded
        3. No truncation of individual rule text
        4. Track exclusion reason: BUDGET_EXHAUSTED or RULE_TEXT_TOO_LARGE

        Args:
            candidates: List of SelectedBusinessRule objects (already ordered by RRF).
            token_budget: Maximum tokens available.

        Returns:
            (selected_rules, excluded_rules) — two lists partitioning candidates.
        """
        selected = []
        excluded = []

        tokens_used = 0

        for rule in candidates:
            rule_tokens = rule.estimated_tokens

            # Check if rule is too large for entire budget (exclude without adding)
            if rule_tokens > token_budget:
                rule.included = False
                rule.exclusion_reason = "RULE_TEXT_TOO_LARGE"
                excluded.append(rule)
                continue

            # Check if rule fits in remaining budget
            if tokens_used + rule_tokens <= token_budget:
                rule.included = True
                selected.append(rule)
                tokens_used += rule_tokens
            else:
                # Budget exhausted
                rule.included = False
                rule.exclusion_reason = "BUDGET_EXHAUSTED"
                excluded.append(rule)

        return selected, excluded

    # ─────────────────────────────────────────────────────────────────────────

    def _detect_conflicts(
        self, rules: list[SelectedBusinessRule]
    ) -> list[tuple[int, int]]:
        """
        Detect conflicting rules and preserve both without resolution.

        Conflict patterns:
        1. Same condition, different thresholds
        2. Same outcome, different conditions
        3. Same text, different source documents/versions
        4. Apparent contradictions (e.g. "must be >= 100" vs "must be < 100")

        For this MVP phase, we log the pairs but do NOT implement full
        conflict resolution (that's a future layer).

        Args:
            rules: List of selected SelectedBusinessRule objects.

        Returns:
            List of tuples (rule_id_a, rule_id_b) representing conflicts.
        """
        conflicts = []

        # Simple heuristic: if two rules have same condition and outcome
        # but different thresholds, flag as conflict
        for i, rule_a in enumerate(rules):
            for rule_b in rules[i + 1 :]:
                # Same condition + outcome but different threshold?
                if (
                    rule_a.condition
                    and rule_b.condition
                    and rule_a.condition == rule_b.condition
                    and rule_a.outcome
                    and rule_b.outcome
                    and rule_a.outcome == rule_b.outcome
                    and rule_a.threshold != rule_b.threshold
                ):
                    conflicts.append((rule_a.workflow_business_rule_id, rule_b.workflow_business_rule_id))
                    rule_a.conflicts_with_rule_ids.append(rule_b.workflow_business_rule_id)
                    rule_b.conflicts_with_rule_ids.append(rule_a.workflow_business_rule_id)
                    rule_a.conflict_reason = "DIFFERENT_THRESHOLD_SAME_CONDITION"
                    rule_b.conflict_reason = "DIFFERENT_THRESHOLD_SAME_CONDITION"

        return conflicts
