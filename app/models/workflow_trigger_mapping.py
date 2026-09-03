from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.workflow_action_mapping import MappingStatus


class WorkflowTriggerMapping(Base):
    __tablename__ = "workflow_trigger_mapping"

    id = Column(Integer, primary_key=True)

    workflow_knowledge_id = Column(
        Integer,
        ForeignKey("workflow_knowledge.id"),
        nullable=False,
    )

    # ── BRD-extracted fields ──────────────────────────────────────────────────
    # Raw name extracted from the BRD document
    extracted_name = Column(String, nullable=False)

    # BRD-extracted description of this trigger
    description = Column(Text)

    matched_trigger_definition_id = Column(
        Integer,
        ForeignKey("trigger_definitions.id"),
        nullable=True,
    )

    status = Column(
        Enum(MappingStatus, name="mappingstatus"),
        nullable=False,
        default=MappingStatus.PENDING,
    )

    similarity_score = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ── Snapshot of TriggerDefinition at mapping time ─────────────────────────
    # Copied from TriggerDefinition when matched_trigger_definition_id is set.
    # Generation reads these columns — TriggerDefinition is never queried during
    # workflow generation.
    # NULL on legacy rows; falls back to trigger_definition relationship.

    # Catalog trigger name — used as the trigger key in the generated DAG
    trigger_name = Column(String, nullable=True)

    # Human-readable label from catalog
    display_name = Column(String, nullable=True)

    # Catalog-level description (NOT the BRD-extracted description above)
    catalog_description = Column(Text, nullable=True)

    # Searchable aliases from catalog
    aliases = Column(JSONB, nullable=True)

    # Domain classification (e.g. "finance")
    workflow_type = Column(String, nullable=True)

    # ── BRD-extracted business context ───────────────────────────────────────
    # Written at ingestion time from the LLM extraction response.
    # These link this specific trigger to the rules and actors that govern it
    # within the BRD — not workspace-wide rules, only those explicitly tied
    # to this trigger in the source document.

    # Business rules from the BRD that apply specifically to this trigger.
    # e.g. ["Application must be submitted by the account holder only"]
    applicable_rules = Column(JSONB, nullable=True)

    # Actors responsible for or involved in this trigger event.
    # e.g. ["Customer (initiator)", "Relationship Manager (validator)"]
    responsible_actors = Column(JSONB, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    workflow = relationship(
        "WorkflowKnowledge",
        back_populates="trigger",
    )

    # Fallback for legacy rows that predate snapshot columns
    trigger_definition = relationship("TriggerDefinition")
