from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base

from pgvector.sqlalchemy import Vector

class ActionDefinition(Base):
    __tablename__ = "action_definitions"

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False, unique=True)

    display_name = Column(String, nullable=False)

    description = Column(Text)

    workflow_type = Column(String, nullable=False)

    aliases = Column(JSONB, nullable=False, default=list)

    config_schema = Column(JSONB)

    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime)

    updated_at = Column(DateTime)
    
    embedding = Column(Vector(384), nullable=True)

    # Python function name in the dispatcher ACTION_MAP.
    # When set, the dispatcher uses this name to resolve the handler,
    # allowing DB aliases to map to canonical function names without code changes.
    handler_name = Column(String, nullable=True)