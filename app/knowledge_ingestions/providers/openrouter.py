"""
app/knowledge_ingestions/providers/openrouter.py

OpenRouter implementation of TextProvider.

Used as the TEXT_PROVIDER fallback when Gemini is rate-limited (429).
Routes to any OpenRouter-supported model; defaults to gpt-4o-mini.

Env vars (shared with app/nlp/llm_manager/providers/openrouter.py):
    OPEN_ROUTER_KEY      — required
    OPENROUTER_MODEL     — default: openai/gpt-4o-mini
    OPENROUTER_TIMEOUT   — default: 60
"""

import os
import time

import requests
from dotenv import load_dotenv

from app.core.logger import logger
from app.knowledge_ingestions.providers.base import TextProvider, TextProviderError

load_dotenv()

_API_KEY  = os.getenv("OPEN_ROUTER_KEY", "")
_MODEL    = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
_TIMEOUT  = int(os.getenv("OPENROUTER_TIMEOUT", "60"))
_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
_FATAL    = {401, 403}


class OpenRouterTextProvider(TextProvider):
    """
    TextProvider backed by OpenRouter.

    Used for appendix extraction and any text-only supplementary pass
    when Gemini is unavailable or rate-limited.
    """

    @property
    def provider_name(self) -> str:
        return f"openrouter-text:{_MODEL}"

    def generate(self, prompt: str) -> str:
        if not _API_KEY:
            raise TextProviderError(
                self.provider_name,
                "OPEN_ROUTER_KEY is not set",
                retryable=False,
            )

        headers = {
            "Authorization": f"Bearer {_API_KEY}",
            "Content-Type":  "application/json",
            "X-Title":       "mflows",
        }
        payload = {
            "model":    _MODEL,
            "messages": [{"role": "user", "content": prompt}],
        }

        start = time.time()
        try:
            response = requests.post(
                _BASE_URL,
                headers=headers,
                json=payload,
                timeout=_TIMEOUT,
            )
        except requests.Timeout:
            raise TextProviderError(
                self.provider_name,
                f"request timed out after {_TIMEOUT}s",
                retryable=True,
            )
        except Exception as exc:
            raise TextProviderError(
                self.provider_name,
                str(exc),
                retryable=True,
            )

        latency_ms = int((time.time() - start) * 1000)

        if response.status_code in _FATAL:
            raise TextProviderError(
                self.provider_name,
                f"HTTP {response.status_code}: auth error",
                retryable=False,
            )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 0
            retryable = status not in _FATAL
            raise TextProviderError(
                self.provider_name,
                f"HTTP {status}: {exc}",
                retryable=retryable,
            )

        data = response.json()
        text = data["choices"][0]["message"]["content"]

        # Strip markdown fences
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        logger.debug(
            "openrouter_text_provider_success",
            extra={"extra_data": {"latency_ms": latency_ms, "model": _MODEL}},
        )
        return text
