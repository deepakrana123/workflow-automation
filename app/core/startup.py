"""
app/core/startup.py

Startup health checks and warm-up tasks.
All checks are non-fatal — the app starts regardless.
Failures are logged clearly so deployment platforms can detect them.
"""

from app.core.logger import logger


def check_database() -> dict:
    """Verify DB connection is reachable."""
    try:
        from sqlalchemy import text
        from app.db.session import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("startup_db_ok")
        return {"status": "ok"}
    except Exception as e:
        logger.error("startup_db_failed", extra={"extra_data": {"error": str(e)[:200]}})
        return {"status": "error", "error": str(e)[:200]}


def check_redis() -> dict:
    """Verify Redis connection is reachable."""
    try:
        from app.core.redis_client import redis_client
        redis_client.ping()
        logger.info("startup_redis_ok")
        return {"status": "ok"}
    except Exception as e:
        logger.error("startup_redis_failed", extra={"extra_data": {"error": str(e)[:200]}})
        return {"status": "error", "error": str(e)[:200]}


def check_embedding_model() -> dict:
    """
    Warm up the embedding model by running a dummy encode.
    Loads the model into memory so the first real request is fast.
    """
    try:
        from app.semantic.embedding_service import EmbeddingService
        svc = EmbeddingService()
        svc.generate_embedding("warmup")
        logger.info("startup_embedding_model_ok")
        return {"status": "ok"}
    except Exception as e:
        logger.error("startup_embedding_model_failed", extra={"extra_data": {"error": str(e)[:200]}})
        return {"status": "error", "error": str(e)[:200]}


def run_startup_checks() -> dict:
    """
    Run all startup checks. Returns a summary dict.
    Called once on app startup via lifespan.
    """
    logger.info("startup_checks_starting")

    results = {
        "database":        check_database(),
        "redis":           check_redis(),
        "embedding_model": check_embedding_model(),
    }

    failed = [k for k, v in results.items() if v["status"] != "ok"]
    if failed:
        logger.warning(
            "startup_checks_partial",
            extra={"extra_data": {"failed": failed, "results": {
                k: v["status"] for k, v in results.items()
            }}},
        )
    else:
        logger.info("startup_checks_all_ok")

    return results


# Module-level cache — populated once at startup, read by health endpoint
_startup_results: dict = {}
