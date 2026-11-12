
from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.db.base import Base


class WorkflowRuleMetadata(Base):
    __tablename__ = "workflow_rule_metadata"

    __table_args__ = (
        UniqueConstraint("rule_id", name="uq_workflow_rule_metadata_rule_id"),
        CheckConstraint(
            "policy_level IS NULL OR policy_level IN "
            "('GLOBAL', 'ZONE', 'REGION', 'BRANCH')",
            name="ck_rule_metadata_policy_level",
        ),
        CheckConstraint(
            "status IS NULL OR status IN "
            "('ACTIVE', 'EXPIRED', 'PROPOSED', 'UNKNOWN')",
            name="ck_rule_metadata_status",
        ),
    )

    id = Column(Integer, primary_key=True)

    rule_id = Column(
        Integer,
        ForeignKey("workflow_business_rule.id", ondelete="CASCADE"),
        nullable=False,
    )

    policy_id = Column(String, nullable=True, index=True)
    policy_level = Column(String, nullable=True, index=True)

    product = Column(String, nullable=True, index=True)
    zone = Column(String, nullable=True, index=True)
    applicant_type = Column(String, nullable=True, index=True)

    rule_type = Column(String, nullable=True, index=True)
    status = Column(String, nullable=True, index=True)

    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)

    metadata_source = Column(String, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
