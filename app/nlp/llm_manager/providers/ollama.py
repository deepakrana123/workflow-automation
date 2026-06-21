import requests
import os
import time

from app.core.logger import logger

OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_URL = f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate"
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "1sss"))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")


def try_call_ollama(prompt: str) -> dict:
    start = time.time()
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=OLLAMA_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        latency_ms = int((time.time() - start) * 1000)

        logger.info(
            "ollama_call_success",
            extra={"extra_data": {"latency_ms": latency_ms}},
        )
        return {
            "success": True,
            "output": data["response"],
            "provider": "ollama",
            "latency_ms": latency_ms,
            "error_type": None,
        }

    except requests.Timeout:
        latency_ms = int((time.time() - start) * 1000)
        logger.warning(
            "ollama_timeout",
            extra={"extra_data": {"timeout_seconds": OLLAMA_TIMEOUT}},
        )
        return {
            "success": False,
            "provider": "ollama",
            "error": f"timeout after {OLLAMA_TIMEOUT}s",
            "error_type": "timeout",
            "latency_ms": latency_ms,
        }

    except requests.ConnectionError as e:
        latency_ms = int((time.time() - start) * 1000)
        logger.warning(
            "ollama_connection_error",
            extra={"extra_data": {"error": str(e)[:120]}},
        )
        return {
            "success": False,
            "provider": "ollama",
            "error": str(e),
            "error_type": "connection_error",
            "latency_ms": latency_ms,
        }

    except requests.HTTPError as e:
        latency_ms = int((time.time() - start) * 1000)
        status_code = e.response.status_code if e.response is not None else None
        error_type = "auth_error" if status_code in (401, 403) else "http_error"
        logger.warning(
            "ollama_http_error",
            extra={"extra_data": {"status_code": status_code}},
        )
        return {
            "success": False,
            "provider": "ollama",
            "error": str(e),
            "error_type": error_type,
            "latency_ms": latency_ms,
        }

    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        logger.error(
            "ollama_unexpected_error",
            extra={"extra_data": {"error": str(e)[:200]}},
        )
        return {
            "success": False,
            "provider": "ollama",
            "error": str(e),
            "error_type": "unexpected",
            "latency_ms": latency_ms,
        }
