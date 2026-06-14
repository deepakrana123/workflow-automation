import requests
import os
import time

from app.core.logger import logger

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "10"))

URL = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/{MODEL}:generateContent?key={API_KEY}"
)

# These HTTP status codes permanently disable the provider until cooldown
FATAL_STATUS_CODES = {401, 403}


def try_call_gemini_rest(prompt: str) -> dict:
    start = time.time()
    try:
        response = requests.post(
            URL,
            json={
                "contents": [
                    {"parts": [{"text": prompt}]}
                ]
            },
            timeout=GEMINI_TIMEOUT,
        )

        # Surface auth errors explicitly before raise_for_status
        # so the health tracker can classify them as fatal
        if response.status_code in FATAL_STATUS_CODES:
            latency_ms = int((time.time() - start) * 1000)
            logger.warning(
                "gemini_auth_error",
                extra={"extra_data": {"status_code": response.status_code}},
            )
            return {
                "success": False,
                "provider": "gemini",
                "error": f"auth_error:{response.status_code}",
                "error_type": "auth_error",
                "latency_ms": latency_ms,
            }

        response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        latency_ms = int((time.time() - start) * 1000)

        logger.info(
            "gemini_call_success",
            extra={"extra_data": {"latency_ms": latency_ms}},
        )
        return {
            "success": True,
            "provider": "gemini",
            "output": text,
            "latency_ms": latency_ms,
            "error_type": None,
        }

    except requests.Timeout:
        latency_ms = int((time.time() - start) * 1000)
        logger.warning(
            "gemini_timeout",
            extra={"extra_data": {"timeout_seconds": GEMINI_TIMEOUT}},
        )
        return {
            "success": False,
            "provider": "gemini",
            "error": f"timeout after {GEMINI_TIMEOUT}s",
            "error_type": "timeout",
            "latency_ms": latency_ms,
        }

    except requests.HTTPError as e:
        latency_ms = int((time.time() - start) * 1000)
        status_code = e.response.status_code if e.response is not None else None
        error_type = "auth_error" if status_code in FATAL_STATUS_CODES else "http_error"
        logger.warning(
            "gemini_http_error",
            extra={"extra_data": {"status_code": status_code}},
        )
        return {
            "success": False,
            "provider": "gemini",
            "error": str(e),
            "error_type": error_type,
            "latency_ms": latency_ms,
        }

    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        logger.error(
            "gemini_unexpected_error",
            extra={"extra_data": {"error": str(e)[:200]}},
        )
        return {
            "success": False,
            "provider": "gemini",
            "error": str(e),
            "error_type": "unexpected",
            "latency_ms": latency_ms,
        }
