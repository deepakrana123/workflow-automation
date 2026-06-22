from fastapi import APIRouter
from app.nlp.llm_manager.llm_manager import LLMManager
from app.nlp.llm_manager import provider_health as health
from app.core import startup as startup_module

router = APIRouter(prefix="/health", tags=["health"])

_manager = LLMManager()


@router.get("/")
def system_health():
    """
    Full system health — DB, Redis, embedding model, LLM providers.
    Used by deployment platforms for liveness/readiness checks.
    """
    startup = startup_module._startup_results

    db_ok    = startup.get("database", {}).get("status") == "ok"
    redis_ok = startup.get("redis", {}).get("status") == "ok"
    embed_ok = startup.get("embedding_model", {}).get("status") == "ok"

    overall = "ok" if (db_ok and redis_ok) else "degraded"

    return {
        "status": overall,
        "service": "mflows",
        "checks": {
            "database":        startup.get("database",        {"status": "unknown"}),
            "redis":           startup.get("redis",           {"status": "unknown"}),
            "embedding_model": startup.get("embedding_model", {"status": "unknown"}),
        },
    }


@router.get("/providers")
def provider_health():
    """LLM provider health state — enabled/disabled, cooldown, failure count."""
    return _manager.get_health_status()


@router.get("/ready")
def readiness():
    """
    Readiness check — returns 200 only if DB and Redis are healthy.
    Use this as the readiness probe in Railway/Render/K8s.
    """
    startup = startup_module._startup_results
    db_ok    = startup.get("database", {}).get("status") == "ok"
    redis_ok = startup.get("redis", {}).get("status") == "ok"

    if db_ok and redis_ok:
        return {"ready": True}

    from fastapi import HTTPException
    raise HTTPException(
        status_code=503,
        detail={
            "ready": False,
            "database": startup.get("database", {}).get("status"),
            "redis": startup.get("redis", {}).get("status"),
        }
    )


@router.post("/providers/{provider_name}/reset")
def reset_provider(provider_name: str):
    """Manually re-enable a disabled LLM provider."""
    _manager.reset_provider(provider_name)
    return {
        "success": True,
        "provider": provider_name,
        "message": f"Provider '{provider_name}' manually re-enabled.",
    }
