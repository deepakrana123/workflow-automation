import time
import random
from app.core.logger import logger


def with_retry(fn, retries=3, base_delay=1, max_delay=8):
    last_result = None
    for attempt in range(retries):
        result = fn()
        if result["success"]:
            result["retries_used"] = attempt
            if attempt > 0:
                logger.info(
                    "retry_succeeded",
                    extra={"extra_data": {"attempt": attempt, "retries_used": attempt}},
                )
            return result

        last_result = result
        error_text = str(result.get("error", "")).lower()
        retryable = any(
            word in error_text
            for word in ["timeout", "429", "500", "502", "503", "connection"]
        )

        if not retryable:
            logger.warning(
                "retry_non_retryable_error",
                extra={
                    "extra_data": {
                        "attempt": attempt,
                        "error": result.get("error"),
                    }
                },
            )
            result["retries_used"] = attempt
            return result

        if attempt < retries - 1:
            delay = min(base_delay * (2**attempt), max_delay)
            jitter = random.uniform(0, 0.5)
            logger.warning(
                "retry_attempt",
                extra={
                    "extra_data": {
                        "attempt": attempt + 1,
                        "max_retries": retries,
                        "delay_seconds": round(delay + jitter, 2),
                        "error": result.get("error"),
                    }
                },
            )
            time.sleep(delay + jitter)

    logger.error(
        "retry_all_attempts_exhausted",
        extra={
            "extra_data": {"retries": retries, "last_error": last_result.get("error")}
        },
    )
    last_result["retries_used"] = retries
    return last_result
