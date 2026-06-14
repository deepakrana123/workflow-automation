"""
app/repositories/generation_log_repo.py

Write and query generation log rows.
All writes are fire-and-forget — never raise, never block the generation path.
"""

from sqlalchemy.orm import Session
from app.models.generation_log import GenerationLog
from app.core.logger import logger


def save(
    db: Session,
    *,
    user_request: str,
    domain: str | None,
    prompt_name: str,
    prompt_version: str,
    estimated_tokens: int | None,
    provider: str | None,
    attempt_number: int,
    is_fallback: bool,
    success: bool,
    failure_reason: str | None,
    errors: list | None,
    latency_ms: int | None,
) -> None:
    """
    Write one generation log row.
    Silently swallows exceptions so a logging failure never crashes generation.
    """
    try:
        log = GenerationLog(
            user_request=user_request[:500],
            domain=domain,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            estimated_tokens=estimated_tokens,
            provider=provider,
            attempt_number=attempt_number,
            is_fallback=is_fallback,
            success=success,
            failure_reason=failure_reason,
            errors=errors,
            latency_ms=latency_ms,
        )
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(
            "generation_log_write_failed",
            extra={"extra_data": {"error": str(e)[:200]}},
        )


def get_stats_by_version(db: Session) -> list[dict]:
    """
    Returns pass rate, avg retries, avg latency grouped by prompt_version.
    Used by GET /api/prompts/stats.
    """
    from sqlalchemy import func, case

    rows = (
        db.query(
            GenerationLog.prompt_version,
            GenerationLog.prompt_name,
            func.count(GenerationLog.id).label("total"),
            func.sum(
                case((GenerationLog.success == True, 1), else_=0)
            ).label("passed"),
            func.avg(GenerationLog.attempt_number).label("avg_attempts"),
            func.avg(GenerationLog.latency_ms).label("avg_latency_ms"),
        )
        .group_by(GenerationLog.prompt_version, GenerationLog.prompt_name)
        .order_by(GenerationLog.prompt_name, GenerationLog.prompt_version)
        .all()
    )

    return [
        {
            "prompt_name": r.prompt_name,
            "prompt_version": r.prompt_version,
            "total": r.total,
            "passed": r.passed,
            "pass_rate": round(r.passed / r.total, 3) if r.total else 0,
            "avg_attempts": round(float(r.avg_attempts or 0), 2),
            "avg_latency_ms": round(float(r.avg_latency_ms or 0)),
        }
        for r in rows
    ]


def get_recent_failures(db: Session, prompt_name: str, limit: int = 10) -> list[dict]:
    """
    Returns last N failed attempts for a given prompt_name.
    Used by auto-rollback trigger.
    """
    rows = (
        db.query(GenerationLog)
        .filter(
            GenerationLog.prompt_name == prompt_name,
            GenerationLog.success == False,
        )
        .order_by(GenerationLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "prompt_version": r.prompt_version,
            "failure_reason": r.failure_reason,
            "attempt_number": r.attempt_number,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
