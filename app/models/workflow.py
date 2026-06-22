from sqlalchemy import Column, Integer, String, DateTime
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

    status = Column(String(50), nullable=False, default="active", index=True)

    priority = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
