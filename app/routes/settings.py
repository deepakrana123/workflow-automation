"""
app/routes/settings.py

Exposes read-only platform settings derived from environment config.
PUT is accepted but currently a no-op (settings are env-based, not DB-stored).
"""

import os
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/settings", tags=["settings"])


class LLMProviderSettings(BaseModel):
    provider: str = "ollama"
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048


class EmbeddingProviderSettings(BaseModel):
    provider: str = "none"
    model: str = ""
    dimensions: int = 1536


class QueueSettings(BaseModel):
    max_concurrent: int = 5
    max_queue_size: int = 100
    polling_interval_ms: int = 5000


class RetryPolicySettings(BaseModel):
    max_retries: int = 5
    backoff_type: str = "exponential"
    initial_delay_ms: int = 30000
    max_delay_ms: int = 300000


class ExecutionLimits(BaseModel):
    max_execution_time_ms: int = 300000
    max_step_time_ms: int = 60000
    max_payload_size_bytes: int = 1048576


class SettingsResponse(BaseModel):
    llm_provider: LLMProviderSettings
    embedding_provider: EmbeddingProviderSettings
    queue_settings: QueueSettings
    retry_policy: RetryPolicySettings
    execution_limits: ExecutionLimits


def _current_settings() -> dict:
    return {
        "llm_provider": {
            "provider": "ollama" if os.getenv("OLLAMA_URL") else "gemini",
            "model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
            "temperature": 0.7,
            "max_tokens": 2048,
        },
        "embedding_provider": {
            "provider": "none",
            "model": "",
            "dimensions": 1536,
        },
        "queue_settings": {
            "max_concurrent": 5,
            "max_queue_size": 100,
            "polling_interval_ms": 5000,
        },
        "retry_policy": {
            "max_retries": 5,
            "backoff_type": "exponential",
            "initial_delay_ms": 30000,
            "max_delay_ms": 300000,
        },
        "execution_limits": {
            "max_execution_time_ms": 300000,
            "max_step_time_ms": 60000,
            "max_payload_size_bytes": 1048576,
        },
    }


@router.get("")
def get_settings():
    return _current_settings()


@router.put("")
def update_settings(body: dict):
    # Settings are env-based — accept the request but return current state
    return _current_settings()
