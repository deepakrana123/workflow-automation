from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.sql import func

from app.db.base import Base
from sqlalchemy.orm import relationship



class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False, unique=True)

    display_name = Column(String, nullable=False)

    description = Column(String, nullable=True)

    organization_name = Column(String, nullable=True)

    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    workflows = relationship(
    "WorkflowKnowledge",
    back_populates="workspace",
    cascade="all, delete-orphan",
)