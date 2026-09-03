"""
app/models/workflow_chain.py

WorkflowChain — a detected or accepted connection between two workflows.

A chain represents one of:
  - Sequential:   Workflow A terminal step → Workflow B trigger fires
  - Conditional:  Workflow A step under a condition → Workflow B trigger fires
  - Rule-mention: A business rule on a step explicitly references another workflow

Status lifecycle:
  suggested  — auto-detected, not yet reviewed
  accepted   — user confirmed; on_*_dispatch written into source step config
  rejected   — user dismissed; never written to DAG
  auto       — system-applied without user review (high-confidence name_match)
"""

import enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ChainMatchType(str, enum.Enum):
    name_match   = "name_match"    # terminal action name == target trigger name exactly
    fts_match    = "fts_match"     # full-text similarity above threshold
    rule_mention = "rule_mention"  # applicable_rule text mentions target trigger/workflow


class ChainStatus(str, enum.Enum):
    suggested = "suggested"
    accepted  = "accepted"
    rejected  = "rejected"
    auto      = "auto"


class WorkflowChain(Base):
    __tablename__ = "workflow_chains"

    id = Column(Integer, primary_key=True)

    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )

    # Source workflow — where the chain originates
    source_workflow_id = Column(
        Integer,
        ForeignKey("workflows.id"),
        nullable=False,
        index=True,
    )

    # The step in the source DAG whose completion fires the chain
    source_step_id = Column(String, nullable=False)        # DAG step "id" field
    source_action  = Column(String, nullable=False)        # action name at that step

    # Target workflow — what gets dispatched
    target_workflow_id = Column(
        Integer,
        ForeignKey("workflows.id"),
        nullable=False,
        index=True,
    )

    # The trigger event_type of the target workflow
    target_trigger = Column(String, nullable=False)

    # How the connection was detected
    match_type = Column(
        Enum(ChainMatchType, name="chainmatchtype"),
        nullable=False,
    )

    # Confidence: 1.0 for exact name match, lower for FTS/rule mention
    confidence = Column(Float, nullable=False, default=1.0)

    # Current review status
    status = Column(
        Enum(ChainStatus, name="chainstatus"),
        nullable=False,
        default=ChainStatus.suggested,
    )

    # Optional note from user when accepting/rejecting
    note = Column(Text, nullable=True)

    detected_at = Column(
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
    source_workflow = relationship(
        "Workflow",
        foreign_keys=[source_workflow_id],
    )
    target_workflow = relationship(
        "Workflow",
        foreign_keys=[target_workflow_id],
    )
