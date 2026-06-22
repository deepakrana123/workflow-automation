from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class WorkflowRun(Base):
    """
    Business-level workflow run tracking.
    One row per user-triggered execution — used for dashboard, history, audit.
    """

    __tablename__ = "workflow_runs"

    id = Column(BigInteger, primary_key=True, index=True)

    workflow_id = Column(
        BigInteger,
        ForeignKey("workflows.id"),
        nullable=False,
        index=True,
    )

    entity_id = Column(String(255), nullable=True, index=True)
    event_type = Column(String(100), nullable=True, index=True)

    status = Column(String(30), default="QUEUED", nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error_text = Column(Text, nullable=True)
