"""
app/nlp/llm_manager/providers/openai_provider.py

OpenAI provider — standard chat completions.

Env vars:
    OPENAI_API_KEY   — required
    OPENAI_MODEL     — default: gpt-4o-mini
    OPENAI_TIMEOUT   — default: 60
"""

import os
import time

import requests
from dotenv import load_dotenv

from app.core.logger import logger

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "60"))

BASE_URL = "https://api.openai.com/v1/chat/completions"

FATAL_STATUS_CODES = {401, 403}


def try_call_openai(prompt: str) -> dict:
    start = time.time()

    if not API_KEY:
        return {
            "success":    False,
            "provider":   "openai",
            "error":      "OPENAI_API_KEY is not set",
            "error_type": "auth_error",
            "latency_ms": 0,
        }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type":  "application/json",
    }

    payload = {
        "model":    MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        response = requests.post(
            BASE_URL,
            headers=headers,
            json=payload,
            timeout=TIMEOUT,
        )

        if response.status_code in FATAL_STATUS_CODES:
            latency_ms = int((time.time() - start) * 1000)
            logger.warning(
                "openai_auth_error",
                extra={"extra_data": {"status_code": response.status_code}},
            )
            return {
                "success":    False,
                "provider":   "openai",
                "error":      f"auth_error:{response.status_code}",
                "error_type": "auth_error",
                "latency_ms": latency_ms,
            }

        response.raise_for_status()
        data       = response.json()
        text       = data["choices"][0]["message"]["content"]
        output     = _clean_output(text)
        latency_ms = int((time.time() - start) * 1000)

        logger.info(
            "openai_call_success",
            extra={"extra_data": {"model": MODEL, "latency_ms": latency_ms}},
        )
        return {
            "success":    True,
            "provider":   "openai",
            "output":     output,
            "latency_ms": latency_ms,
            "error_type": None,
        }

    except requests.Timeout:
        latency_ms = int((time.time() - start) * 1000)
        logger.warning("openai_timeout", extra={"extra_data": {"timeout": TIMEOUT}})
        return {
            "success":    False,
            "provider":   "openai",
            "error":      f"timeout after {TIMEOUT}s",
            "error_type": "timeout",
            "latency_ms": latency_ms,
        }

    except requests.HTTPError as e:
        latency_ms  = int((time.time() - start) * 1000)
        status_code = e.response.status_code if e.response is not None else None
        error_type  = "auth_error" if status_code in FATAL_STATUS_CODES else "http_error"
        logger.warning(
            "openai_http_error",
            extra={"extra_data": {"status_code": status_code, "error": str(e)[:200]}},
        )
        return {
            "success":    False,
            "provider":   "openai",
            "error":      str(e),
            "error_type": error_type,
            "latency_ms": latency_ms,
        }

    except Exception as e:  # noqa: BLE001
        latency_ms = int((time.time() - start) * 1000)
        logger.error("openai_unexpected_error", extra={"extra_data": {"error": str(e)[:200]}})
        return {
            "success":    False,
            "provider":   "openai",
            "error":      str(e),
            "error_type": "unexpected",
            "latency_ms": latency_ms,
        }


def _clean_output(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()
