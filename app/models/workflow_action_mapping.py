import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

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

    extract_name = Column(String, nullable=False)

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

    # Relationships
    workflow = relationship(
        "WorkflowKnowledge",
        back_populates="actions",
    )

    action_definition = relationship("ActionDefinition")
