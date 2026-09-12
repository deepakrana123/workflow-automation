"""
app/nlp/llm_manager/providers/groq.py

Groq provider — OpenAI-compatible REST API, extremely fast inference.

Env vars:
    GROQ_API_KEY   — required
    GROQ_MODEL     — default: llama-3.3-70b-versatile
    GROQ_TIMEOUT   — default: 30
"""

import os
import time

import requests
from dotenv import load_dotenv

from app.core.logger import logger

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY", "")  # must be set explicitly — no fallback to other keys
MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
TIMEOUT = int(os.getenv("GROQ_TIMEOUT", "30"))

BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

FATAL_STATUS_CODES = {401, 403}


def try_call_groq(prompt: str) -> dict:
    start = time.time()

    if not API_KEY:
        return {
            "success":    False,
            "provider":   "groq",
            "error":      "GROQ_API_KEY is not set",
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
                "groq_auth_error",
                extra={"extra_data": {"status_code": response.status_code}},
            )
            return {
                "success":    False,
                "provider":   "groq",
                "error":      f"auth_error:{response.status_code}",
                "error_type": "auth_error",
                "latency_ms": latency_ms,
            }

        response.raise_for_status()
        data      = response.json()
        text      = data["choices"][0]["message"]["content"]
        output    = _clean_output(text)
        latency_ms = int((time.time() - start) * 1000)

        logger.info(
            "groq_call_success",
            extra={"extra_data": {"model": MODEL, "latency_ms": latency_ms}},
        )
        return {
            "success":    True,
            "provider":   "groq",
            "output":     output,
            "latency_ms": latency_ms,
            "error_type": None,
        }

    except requests.Timeout:
        latency_ms = int((time.time() - start) * 1000)
        logger.warning("groq_timeout", extra={"extra_data": {"timeout": TIMEOUT}})
        return {
            "success":    False,
            "provider":   "groq",
            "error":      f"timeout after {TIMEOUT}s",
            "error_type": "timeout",
            "latency_ms": latency_ms,
        }

    except requests.HTTPError as e:
        latency_ms  = int((time.time() - start) * 1000)
        status_code = e.response.status_code if e.response is not None else None
        error_type  = "auth_error" if status_code in FATAL_STATUS_CODES else "http_error"
        logger.warning(
            "groq_http_error",
            extra={"extra_data": {"status_code": status_code, "error": str(e)[:200]}},
        )
        return {
            "success":    False,
            "provider":   "groq",
            "error":      str(e),
            "error_type": error_type,
            "latency_ms": latency_ms,
        }

    except Exception as e:  # noqa: BLE001
        latency_ms = int((time.time() - start) * 1000)
        logger.error("groq_unexpected_error", extra={"extra_data": {"error": str(e)[:200]}})
        return {
            "success":    False,
            "provider":   "groq",
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
