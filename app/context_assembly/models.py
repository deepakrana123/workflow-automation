"""
app/context_assembly/models.py

Data transfer objects (DTOs) for context assembly and source traceability.

These models represent:
1. Individual business rules selected for context
2. Complete context packages ready for LLM consumption
3. Source provenance chains and validation results
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class SourceProvenance:
    """Complete source chain for a single rule.
    
    Validates and represents the provenance from:
      WorkflowBusinessRule → WorkflowKnowledge → DocumentVersion → BRDDocument → Workspace → Tenant
    """

    # WorkflowKnowledge provenance
    workflow_knowledge_id: Optional[int] = None
    workflow_knowledge_name: Optional[str] = None
    workflow_knowledge_summary: Optional[str] = None

    # BRDDocument provenance
    brd_document_id: Optional[int] = None
    brd_document_filename: Optional[str] = None
    brd_document_type: Optional[str] = None  # "brd", "policy", etc.
    brd_document_version: Optional[int] = None

    # DocumentVersion provenance
    document_version_id: Optional[int] = None
    document_version_number: Optional[int] = None
    document_original_filename: Optional[str] = None
    document_storage_path: Optional[str] = None
    document_page_count: Optional[int] = None
    document_sha256_hash: Optional[str] = None
    document_mime_type: Optional[str] = None

    # Source page number (if reliably available from extraction)
    source_page_number: Optional[int] = None

    # Workspace/Tenant isolation verification
    workspace_id: int = 0
    tenant_id: int = 0

    # Completeness tracking
    is_complete: bool = False  # True if full chain: BusinessRule → Document → DocumentVersion
    missing_links: list[str] = field(default_factory=list)  # e.g. ["document_version_id"]

    def __repr__(self) -> str:
        return (
            f"<SourceProvenance "
            f"rule_id=WK{self.workflow_knowledge_id} "
            f"doc=BD{self.brd_document_id}v{self.brd_document_version} "
            f"complete={self.is_complete}>"
        )


@dataclass
class SelectedBusinessRule:
    """One business rule selected for inclusion in assembled context.
    
    Preserves:
    - Raw rule text and metadata
    - Retrieval scoring (vector_rank, bm25_rank, postgres_rank, rrf_score)
    - Complete source provenance
    - Selection reason and exclusion flags
    """

    # Rule identity
    workflow_business_rule_id: int
    workflow_knowledge_id: int

    # Rule content
    rule_text: str
    condition: Optional[str] = None
    outcome: Optional[str] = None
    responsible_role: Optional[str] = None
    threshold: Optional[str] = None

    # Retrieval scores (preserved from RankedCandidate)
    vector_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
    postgres_rank: Optional[int] = None
    rrf_score: float = 0.0
    cross_encoder_score: Optional[float] = None

    # Source provenance (complete chain validation)
    provenance: SourceProvenance = field(default_factory=SourceProvenance)

    # Selection decision
    included: bool = True
    exclusion_reason: Optional[str] = None  # e.g. "RULE_TEXT_TOO_LARGE", "BUDGET_EXHAUSTED"
    estimated_tokens: int = 0

    # Conflict detection
    conflicts_with_rule_ids: list[int] = field(default_factory=list)  # IDs of conflicting rules
    conflict_reason: Optional[str] = None  # e.g. "DIFFERENT_THRESHOLD_SAME_CONDITION"

    def __repr__(self) -> str:
        status = "INCLUDED" if self.included else f"EXCLUDED({self.exclusion_reason})"
        return (
            f"<SelectedBusinessRule "
            f"id={self.workflow_business_rule_id} "
            f"rrf={self.rrf_score:.3f} "
            f"tokens={self.estimated_tokens} "
            f"{status}>"
        )


@dataclass
class AssembledContext:
    """Complete context package ready for LLM consumption.
    
    Contains:
    - Context metadata (query, retrieval config, tenant/workspace)
    - Selected rules with full provenance
    - Token budget tracking
    - Exclusion and conflict analysis
    """

    # Metadata
    tenant_id: int
    workspace_id: int
    query: str
    retrieval_timestamp: datetime = field(default_factory=datetime.utcnow)

    # Retrieval configuration snapshot
    retrieval_model: str = "BAAI/bge-small-en-v1.5"
    retrieval_top_k: int = 50
    rrf_k_constant: int = 60
    token_budget: int = 4000  # Default context budget

    # Selected rules
    selected_rules: list[SelectedBusinessRule] = field(default_factory=list)

    # Excluded candidates (context assembly decision)
    excluded_candidates: list[SelectedBusinessRule] = field(default_factory=list)

    # Token accounting
    total_candidates_retrieved: int = 0
    total_rules_selected: int = 0
    total_rules_excluded: int = 0

    estimated_tokens_used: int = 0
    estimated_tokens_remaining: int = 0

    # Conflict detection
    conflicting_rule_pairs: list[tuple[int, int]] = field(default_factory=list)
    has_conflicts: bool = False

    # Quality indicators
    provenance_completeness_pct: float = 100.0  # % of rules with complete provenance
    rules_with_incomplete_provenance: list[int] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"<AssembledContext "
            f"workspace_id={self.workspace_id} "
            f"selected={self.total_rules_selected} "
            f"excluded={self.total_rules_excluded} "
            f"tokens={self.estimated_tokens_used}/{self.token_budget}>"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "metadata": {
                "tenant_id": self.tenant_id,
                "workspace_id": self.workspace_id,
                "query": self.query,
                "retrieval_timestamp": self.retrieval_timestamp.isoformat(),
                "retrieval_model": self.retrieval_model,
                "retrieval_top_k": self.retrieval_top_k,
                "rrf_k_constant": self.rrf_k_constant,
            },
            "token_budget": {
                "total_budget": self.token_budget,
                "estimated_used": self.estimated_tokens_used,
                "estimated_remaining": self.estimated_tokens_remaining,
            },
            "selection_summary": {
                "total_retrieved": self.total_candidates_retrieved,
                "total_selected": self.total_rules_selected,
                "total_excluded": self.total_rules_excluded,
            },
            "selected_rules": [
                {
                    "rule_id": rule.workflow_business_rule_id,
                    "workflow_knowledge_id": rule.workflow_knowledge_id,
                    "rule_text": rule.rule_text,
                    "condition": rule.condition,
                    "outcome": rule.outcome,
                    "responsible_role": rule.responsible_role,
                    "threshold": rule.threshold,
                    "retrieval_scores": {
                        "vector_rank": rule.vector_rank,
                        "bm25_rank": rule.bm25_rank,
                        "postgres_rank": rule.postgres_rank,
                        "rrf_score": rule.rrf_score,
                        "cross_encoder_score": rule.cross_encoder_score,
                    },
                    "estimated_tokens": rule.estimated_tokens,
                    "provenance": {
                        "workflow_knowledge_id": rule.provenance.workflow_knowledge_id,
                        "brd_document_id": rule.provenance.brd_document_id,
                        "document_version_id": rule.provenance.document_version_id,
                        "document_version_number": rule.provenance.document_version_number,
                        "original_filename": rule.provenance.document_original_filename,
                        "page_number": rule.provenance.source_page_number,
                        "sha256_hash": rule.provenance.document_sha256_hash,
                        "is_complete": rule.provenance.is_complete,
                        "missing_links": rule.provenance.missing_links,
                    },
                    "conflicts": {
                        "conflicts_with_rule_ids": rule.conflicts_with_rule_ids,
                        "conflict_reason": rule.conflict_reason,
                    },
                }
                for rule in self.selected_rules
            ],
            "excluded_rules": [
                {
                    "rule_id": rule.workflow_business_rule_id,
                    "reason": rule.exclusion_reason,
                    "estimated_tokens": rule.estimated_tokens,
                }
                for rule in self.excluded_candidates
            ],
            "conflicts": {
                "has_conflicts": self.has_conflicts,
                "conflicting_pairs": self.conflicting_rule_pairs,
            },
            "provenance_quality": {
                "completeness_pct": self.provenance_completeness_pct,
                "rules_with_incomplete_provenance": self.rules_with_incomplete_provenance,
            },
        }
