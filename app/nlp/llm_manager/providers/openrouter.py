"""
app/nlp/llm_manager/providers/openrouter.py

OpenRouter provider — OpenAI-compatible REST API.

OpenRouter routes to any model (GPT-4o, Claude, Mistral, Llama, etc.)
using a single API key and the standard OpenAI chat completions format.

Env vars:
    OPENROUTER_API_KEY   — required
    OPENROUTER_MODEL     — default: openai/gpt-4o-mini
    OPENROUTER_TIMEOUT   — default: 60
    OPENROUTER_SITE_URL  — optional, sent as HTTP-Referer (recommended by OpenRouter)
    OPENROUTER_APP_NAME  — optional, sent as X-Title
"""

import os
import time

import requests
from dotenv import load_dotenv

from app.core.logger import logger

load_dotenv()

API_KEY  = os.getenv("OPEN_ROUTER_KEY", "")
MODEL    = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
TIMEOUT  = int(os.getenv("OPENROUTER_TIMEOUT", "60"))
SITE_URL = os.getenv("OPENROUTER_SITE_URL", "")
APP_NAME = os.getenv("OPENROUTER_APP_NAME", "mflows")

BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

FATAL_STATUS_CODES = {401, 403}


def try_call_openrouter(prompt: str) -> dict:
    start = time.time()

    if not API_KEY:
        return {
            "success":    False,
            "provider":   "openrouter",
            "error":      "OPEN_ROUTER_KEY is not set",
            "error_type": "auth_error",
            "latency_ms": 0,
        }

    headers = {
        "Authorization":  f"Bearer {API_KEY}",
        "Content-Type":   "application/json",
    }
    if SITE_URL:
        headers["HTTP-Referer"] = SITE_URL
    if APP_NAME:
        headers["X-Title"] = APP_NAME

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
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
                "openrouter_auth_error",
                extra={"extra_data": {"status_code": response.status_code}},
            )
            return {
                "success":    False,
                "provider":   "openrouter",
                "error":      f"auth_error:{response.status_code}",
                "error_type": "auth_error",
                "latency_ms": latency_ms,
            }

        response.raise_for_status()
        data = response.json()

        # OpenRouter returns OpenAI-compatible response shape
        text = data["choices"][0]["message"]["content"]
        output = _clean_output(text)
        latency_ms = int((time.time() - start) * 1000)

        logger.info(
            "openrouter_call_success",
            extra={"extra_data": {
                "model":      MODEL,
                "latency_ms": latency_ms,
            }},
        )
        return {
            "success":    True,
            "provider":   "openrouter",
            "output":     output,
            "latency_ms": latency_ms,
            "error_type": None,
        }

    except requests.Timeout:
        latency_ms = int((time.time() - start) * 1000)
        logger.warning(
            "openrouter_timeout",
            extra={"extra_data": {"timeout": TIMEOUT}},
        )
        return {
            "success":    False,
            "provider":   "openrouter",
            "error":      f"timeout after {TIMEOUT}s",
            "error_type": "timeout",
            "latency_ms": latency_ms,
        }

    except requests.HTTPError as e:
        latency_ms = int((time.time() - start) * 1000)
        status_code = e.response.status_code if e.response is not None else None
        error_type  = "auth_error" if status_code in FATAL_STATUS_CODES else "http_error"
        logger.warning(
            "openrouter_http_error",
            extra={"extra_data": {"status_code": status_code, "error": str(e)[:200]}},
        )
        return {
            "success":    False,
            "provider":   "openrouter",
            "error":      str(e),
            "error_type": error_type,
            "latency_ms": latency_ms,
        }

    except Exception as e:  # noqa: BLE001
        latency_ms = int((time.time() - start) * 1000)
        logger.error(
            "openrouter_unexpected_error",
            extra={"extra_data": {"error": str(e)[:200]}},
        )
        return {
            "success":    False,
            "provider":   "openrouter",
            "error":      str(e),
            "error_type": "unexpected",
            "latency_ms": latency_ms,
        }


def _clean_output(text: str) -> str:
    """Strip markdown code fences if present — same as gemini_rest."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()
