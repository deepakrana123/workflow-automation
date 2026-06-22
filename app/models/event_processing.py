from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func

from app.db.base import Base


class EventProcessing(Base):
    __tablename__ = "event_processing"

    event_id = Column(String, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return (
            f"<EventProcessing("
            f"event_id={self.event_id}, "
            f"status={self.status}"
            f")>"
        )
