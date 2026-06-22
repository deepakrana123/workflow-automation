from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True, nullable=True)
    action = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)

    request_payload = Column(Text, nullable=True)
    response_payload = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
