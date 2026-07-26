from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from pgvector.sqlalchemy import Vector

from app.db.base import Base


class ActionDefinition(Base):
    __tablename__ = "action_definitions"

    id = Column(Integer, primary_key=True)

    name = Column(
        String,
        nullable=False,
        unique=True,
    )

    display_name = Column(
        String,
        nullable=False,
    )

    description = Column(Text)

    workflow_type = Column(
        String,
        nullable=False,
    )

    aliases = Column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Input payload contract
    input_schema = Column(
        JSONB,
        nullable=True,
    )

    # Output payload contract
    output_schema = Column(
        JSONB,
        nullable=True,
    )

    # Default execution template shipped by MFlows
    #
    # Examples:
    #
    # Python:
    # {
    #   "execution_type": "python",
    #   "configuration": {
    #       "handler": "generate_pdf"
    #   }
    # }
    #
    # HTTP:
    # {
    #   "execution_type": "http",
    #   "configuration": {
    #       "method": "POST",
    #       "endpoint": "/payments/create"
    #   }
    # }
    execution_template = Column(
        JSONB,
        nullable=True,
    )

    active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    embedding = Column(
        Vector(384),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )