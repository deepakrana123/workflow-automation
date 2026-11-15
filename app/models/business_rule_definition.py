from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base


class RuleEvaluationStatus(str, enum.Enum):
    """Classification of rule evaluability and runtime behavior.

    Used to distinguish between fully executable rules, informational
    (non-blocking) rules, partially extracted rules that require review,
    unsupported rule patterns, and malformed/invalid rules.

    None (NULL in DB) represents legacy/unknown classification — existing
    rules created before this field was introduced.
    """

    EVALUABLE = "EVALUABLE"         # field, op, value all present and valid
    INFORMATIONAL = "INFORMATIONAL" # policy text, no execution condition
    PARTIAL = "PARTIAL"             # some components missing
    UNSUPPORTED = "UNSUPPORTED"     # pattern recognized but not evaluable
    INVALID = "INVALID"             # malformed extraction, contradictions


_VALID_EVALUATION_STATUSES = tuple(s.value for s in RuleEvaluationStatus)


class BusinessRuleDefinition(Base):
    __tablename__ = "business_rule_definitions"

    __table_args__ = (
        CheckConstraint(
            f"evaluation_status IS NULL OR evaluation_status IN {_VALID_EVALUATION_STATUSES}",
            name="ck_business_rule_evaluation_status",
        ),
    )

    id = Column(Integer, primary_key=True)

    # Level at which this rule is declared.
    # Child workspaces inherit it automatically.
    scope_workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # BRD that this rule was extracted from (nullable — may be manually created)
    source_workflow_knowledge_id = Column(
        Integer,
        ForeignKey("workflow_knowledge.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Provenance: raw rule row ───────────────────────────────────────────────
    # FK to the specific WorkflowBusinessRule row that was parsed to produce
    # this structured definition.
    # NULL for definitions created before this column was introduced, or for
    # manually created rules that have no corresponding raw extraction row.
    # ON DELETE SET NULL — deleting the raw rule does not destroy the
    # structured definition; it simply loses the direct provenance link.
    workflow_business_rule_id = Column(
        Integer,
        ForeignKey("workflow_business_rule.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # The WorkflowContext key this rule reads, e.g. "loan_amount", "credit_score"
    # NULL for description-only rules (still appear in skill.md but not evaluated)
    field = Column(String(255), nullable=True)

    # One of the operators supported by evaluate_condition:
    #   ==, !=, >, >=, <, <=, in, not_in
    op = Column(String(20), nullable=True)

    # Threshold value — numeric, string, or list (stored as JSONB)
    value = Column(JSONB, nullable=True)

    # Original BRD sentence — shown verbatim in skill.md
    description = Column(Text, nullable=False)

    # Roles extracted from the actor clause of the BRD sentence.
    # Used to populate HumanTask.allowed_roles and Capability.required_roles.
    # Example: ["branch_manager", "branch_officer"]
    allowed_roles = Column(JSONB, nullable=True, default=list)

    # If True, lower-level workspaces cannot further restrict this rule.
    # Set on hard global compliance constraints.
    locked = Column(Boolean, nullable=False, default=False)

    active = Column(Boolean, nullable=False, default=True)

    # ── Rule evaluation classification ──────────────────────────────────────────
    # Classification of whether and how this rule can be evaluated at runtime.
    # NULL for legacy rules created before this field was introduced.
    #
    # EVALUABLE    — field, op, value all present and valid; can be evaluated.
    # INFORMATIONAL — policy text with no executable condition; reference only.
    # PARTIAL      — some components missing; requires human review.
    # UNSUPPORTED  — pattern recognized but not evaluable by the runtime engine.
    # INVALID      — malformed extraction (e.g. type mismatches, contradictions).
    evaluation_status = Column(
        String(32),
        nullable=True,
        index=True,
    )

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

    # ── Relationships ─────────────────────────────────────────────────────────

    # Navigation to the raw WorkflowBusinessRule this definition was parsed from.
    # back_populates matches WorkflowBusinessRule.business_rule_definition.
    workflow_business_rule = relationship(
        "WorkflowBusinessRule",
        back_populates="business_rule_definition",
        foreign_keys=[workflow_business_rule_id],
    )

    def is_evaluable(self) -> bool:
        """True if this rule can be evaluated by evaluate_condition at runtime."""
        return bool(self.field and self.op and self.value is not None)
