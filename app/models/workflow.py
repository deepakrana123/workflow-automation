from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base import Base
from sqlalchemy.sql import func


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    domain = Column(String, nullable=False, index=True)
    raw_input = Column(String, nullable=False)
    parsed_rule_json = Column(JSONB, nullable=True)

    # Workspace this workflow belongs to. Nullable — the global generation page
    # (/workflows/generate) produces workspace-less workflows; workspace-scoped
    # generation and synthesis set this so counts/links resolve per workspace.
    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id"),
        nullable=True,
        index=True,
    )

    # Human-readable, deterministic explanation of the generated workflow —
    # derived from the compiled DAG + action/trigger catalog descriptions.
    explanation = Column(JSONB, nullable=True)

    status = Column(String(50), nullable=False, default="active", index=True)

    priority = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
