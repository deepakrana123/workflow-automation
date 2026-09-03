import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pgvector.sqlalchemy import Vector

from app.db.base import Base


class MappingStatus(str, enum.Enum):
    PENDING   = "PENDING"
    MAPPED    = "MAPPED"
    UNMAPPED  = "UNMAPPED"
    FAILED    = "FAILED"


class WorkflowActionMapping(Base):
    __tablename__ = "workflow_action_mapping"

    id = Column(Integer, primary_key=True)

    workflow_knowledge_id = Column(
        Integer,
        ForeignKey("workflow_knowledge.id"),
        nullable=False,
    )

    # ── BRD-extracted fields ──────────────────────────────────────────────────
    extract_name = Column(String, nullable=False)

    # BRD-extracted description of this action (what the document says it does).
    # Distinct from catalog_description below.
    description = Column(Text)

    matched_action_definition_id = Column(
        Integer,
        ForeignKey("action_definitions.id"),
        nullable=True,
    )

    status = Column(
        Enum(MappingStatus, name="mappingstatus"),
        nullable=False,
        default=MappingStatus.PENDING,
    )

    # Raw RRF score of the winning candidate (pre-decision intermediate score)
    similarity_score = Column(Float, nullable=True)

    # sigmoid(cross_encoder_score) — the actual value compared against the threshold
    confidence = Column(Float, nullable=True)

    # Combined query text sent to BM25 and Postgres retrieval
    query_text = Column(Text, nullable=True)

    # Top-K candidates from the full retrieval run, stored for observability.
    # Each entry: {name, rrf_score, cross_encoder_score, vector_rank, bm25_rank, postgres_rank}
    top_candidates = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ── Snapshot of ActionDefinition at mapping time ──────────────────────────
    # Copied from ActionDefinition when matched_action_definition_id is set.
    # These fields are workspace-scoped snapshots — they can be overridden per
    # workspace without touching the global catalog (ActionDefinition).
    # NULL on legacy rows; runtime falls back to action_definition relationship.

    # Catalog action name (ActionDefinition.name) — used as Python handler key
    action_name = Column(String, nullable=True)

    # Human-readable label from catalog
    display_name = Column(String, nullable=True)

    # Catalog-level description (NOT the BRD-extracted description above)
    catalog_description = Column(Text, nullable=True)

    # Searchable aliases from catalog
    aliases = Column(JSONB, nullable=True)

    # Domain classification (e.g. "finance", "insurance")
    workflow_type = Column(String, nullable=True)

    # Input payload contract — what this action expects at runtime
    input_schema = Column(JSONB, nullable=True)

    # Output payload contract — validated after step execution
    output_schema = Column(JSONB, nullable=True)

    # How to execute this action. Copied from ActionDefinition.execution_template.
    # Workspace-specific overrides stored here override the catalog default.
    # Format: {"execution_type": "python", "configuration": {"handler": "..."}}
    execution_template = Column(JSONB, nullable=True)

    # ── BRD-extracted business context ───────────────────────────────────────
    # Written at ingestion time from the LLM extraction response.
    # These link this specific action to the rules and people that govern it
    # within the BRD — not workspace-wide rules, only those explicitly tied
    # to this action in the source document.

    # Business rules from the BRD that apply specifically to this action.
    # e.g. ["Manual approval required above ₹5L", "KYC must be complete first"]
    applicable_rules = Column(JSONB, nullable=True)

    # Actors responsible for or involved in executing this action.
    # e.g. ["Branch Manager (approver)", "Loan Officer (initiator)"]
    responsible_actors = Column(JSONB, nullable=True)

    # ── Workspace-local embedding ─────────────────────────────────────────────
    # Populated in two cases:
    #   1. Automatic: EmbeddingMapper copies ActionDefinition.embedding here
    #      when matched_action_definition_id is set.
    #   2. Manual resolution: UnmappedActionService generates an embedding
    #      directly from action_name + display_name when the workspace owner
    #      fills in values without linking to an ActionDefinition.
    #
    # This embedding is used by WorkspaceCatalogMatcher for vector similarity
    # matching during generation. It lives here — not on ActionDefinition —
    # so workspace-specific naming and context are reflected in the vector.
    embedding = Column(Vector(384), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    workflow = relationship(
        "WorkflowKnowledge",
        back_populates="actions",
    )

    # Still available as a fallback for fields not yet copied / legacy rows
    action_definition = relationship("ActionDefinition")
