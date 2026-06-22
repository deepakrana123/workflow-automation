from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from app.db.base import Base


class TriggerDefinition(Base):
    __tablename__ = "trigger_definitions"

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False, unique=True)

    display_name = Column(String, nullable=False)

    description = Column(Text)

    workflow_type = Column(String, nullable=False)

    aliases = Column(JSONB, nullable=False, default=list)

    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime)

    updated_at = Column(DateTime)
    
    embedding = Column(Vector(384), nullable=True)