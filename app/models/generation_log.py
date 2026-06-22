from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.db.base import Base


class GenerationLog(Base):
    """
    Records every NL workflow generation attempt.
    One row per attempt (not per request — a request with 3 retries = 3 rows).
    Used by the prompt evaluation framework to measure prompt quality.
    """
    __tablename__ = "generation_logs"

    id = Column(BigInteger, primary_key=True)

    # Input
    user_request = Column(Text, nullable=False)
    domain = Column(String(100), nullable=True)

    # Prompt
    prompt_name = Column(String(100), nullable=False)   # e.g. "workflow_generation"
    prompt_version = Column(String(20), nullable=False)  # e.g. "v1", "v2"
    estimated_tokens = Column(Integer, nullable=True)

    # Execution
    provider = Column(String(50), nullable=True)         # "ollama" | "gemini"
    attempt_number = Column(Integer, nullable=False)     # 1, 2, 3 or fallback
    is_fallback = Column(Boolean, nullable=False, default=False)

    # Outcome
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(100), nullable=True)  # schema_fail | dsl_fail | llm_error etc.
    errors = Column(JSONB, nullable=True)
    latency_ms = Column(Integer, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
