
from sqlalchemy import Column, ForeignKey, Integer, Text
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship

from app.db.base import Base

EMBEDDING_DIM = 384


class WorkflowBusinessRule(Base):
    __tablename__ = "workflow_business_rule"

    id = Column(Integer, primary_key=True)

    workflow_knowledge_id = Column(
        Integer,
        ForeignKey("workflow_knowledge.id"),
        nullable=False,
    )

    rule = Column(Text, nullable=False)
    condition = Column(Text, nullable=True)
    outcome = Column(Text, nullable=True)
    responsible_role = Column(Text, nullable=True)
    threshold = Column(Text, nullable=True)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=True)

    # ── Provenance: source document ───────────────────────────────────────────
    # FK to the BRDDocument this rule was extracted from.
    # NULL for rules created before BRDDocument was introduced.
    # ON DELETE SET NULL — deleting the document record does not destroy the
    # extracted rule; it simply loses its source reference.
    source_brd_document_id = Column(
        Integer,
        ForeignKey("brd_documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    # Navigation to the source BRDDocument (read-only, no cascade).
    # No back_populates on BRDDocument — the reverse collection would be large
    # and is not needed by any current query path.
    source_brd_document = relationship(
        "BRDDocument",
        foreign_keys=[source_brd_document_id],
    )

    # Navigation to the structured BusinessRuleDefinition derived from this row.
    # uselist=False — one raw rule produces at most one structured definition.
    # back_populates matches BusinessRuleDefinition.workflow_business_rule.
    business_rule_definition = relationship(
        "BusinessRuleDefinition",
        back_populates="workflow_business_rule",
        uselist=False,
        foreign_keys="BusinessRuleDefinition.workflow_business_rule_id",
    )
