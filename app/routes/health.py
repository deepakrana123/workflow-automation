from fastapi import APIRouter
from app.nlp.llm_manager.llm_manager import LLMManager
from app.nlp.llm_manager import provider_health as health

router = APIRouter(prefix="/health", tags=["health"])

_manager = LLMManager()


@router.get("/")
def system_health():
    """Basic liveness check."""
    return {"status": "ok", "service": "mflows"}


@router.get("/providers")
def provider_health():
    """
    Returns current health state of all LLM providers.

    Example response:
    {
      "ollama": {
        "enabled": false,
        "failure_count": 3,
        "last_error": "timeout after 10s",
        "last_error_type": "timeout",
        "cooldown_remaining_seconds": 243
      },
      "gemini": {
        "enabled": true,
        "failure_count": 0,
        "last_error": null,
        "last_error_type": null,
        "cooldown_remaining_seconds": 0
      }
    }
    """
    return _manager.get_health_status()


@router.post("/providers/{provider_name}/reset")
def reset_provider(provider_name: str):
    """
    Manually re-enable a disabled provider.
    Use for testing or after fixing an auth/config issue.
    """
    _manager.reset_provider(provider_name)
    return {
        "success": True,
        "provider": provider_name,
        "message": f"Provider '{provider_name}' manually re-enabled.",
    }
