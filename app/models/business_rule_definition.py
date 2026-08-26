"""
app/models/business_rule_definition.py

Structured business rule extracted from a BRD.

A WorkflowBusinessRule stores the raw text the LLM pulled from a PDF.
A BusinessRuleDefinition is the parsed, structured form of that text:
it carries a field name, operator, and threshold value that evaluate_condition
can evaluate directly.

The `allowed_roles` column lists the roles (extracted from the actor in the
same BRD sentence) that are the RBAC boundary for this rule. For example:

  BRD text:  "Loan disbursement above ₹5 lakh requires Branch Manager approval"
  →  field:         "loan_amount"
  →  op:            ">="
  →  value:         500000
  →  description:   "Loan disbursement above ₹5 lakh requires Branch Manager approval"
  →  allowed_roles: ["branch_manager"]

`scope_workspace_id` determines which level of the hierarchy this rule is
declared at. Child workspaces inherit all ancestor rules and may only add
more-restrictive rules on top.

`locked = True` means lower-level workspaces cannot narrow this rule further
(used for hard global compliance constraints).
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.db.base import Base


class BusinessRuleDefinition(Base):
    __tablename__ = "business_rule_definitions"

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

    def is_evaluable(self) -> bool:
        """True if this rule can be evaluated by evaluate_condition at runtime."""
        return bool(self.field and self.op and self.value is not None)
