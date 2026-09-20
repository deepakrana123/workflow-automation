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

import base64
import os
import time
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

from app.core.logger import logger
from app.knowledge_ingestions.providers.base import (
    TextProvider,
    TextProviderError,
    VisionProvider,
    VisionProviderError,
)

load_dotenv()

_API_KEY  = os.getenv("OPEN_ROUTER_KEY", "")
_MODEL    = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
_TIMEOUT  = int(os.getenv("OPENROUTER_TIMEOUT", "60"))
_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
_FATAL    = {401, 403}


# ── Vision configuration (separate from the text provider above) ──────────────
# Key resolution prefers OPENROUTER_API_KEY (per the OpenRouter convention) and
# falls back to the project's existing OPEN_ROUTER_KEY for backward compatibility.
# Neither value is ever logged.
_VISION_API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPEN_ROUTER_KEY", "")

# Dedicated vision model var — deliberately NOT OPENROUTER_MODEL (that belongs to
# the text provider). Default is a genuinely FREE ($0/$0) multimodal model that
# accepts image input, verified against OpenRouter's models API.
#
# Chosen default: inclusionai/ling-3.0-flash-vl:free — a native vision-language
# model that, in live testing on a real BRD table page, returned substantial
# extraction on the first attempt where google/gemma-4-26b-a4b-it:free was
# hard rate-limited (HTTP 429 on every attempt) on the same account. The Gemma
# free variant remains a valid override but is throttled far more aggressively.
#
# Keep this configuration-driven: swap it via OPENROUTER_VISION_MODEL if the
# free multimodal landscape or rate limits change.
_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "inclusionai/ling-3.0-flash-vl:free")

# Base URL is configurable; the chat-completions path is appended to it.
_VISION_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
_VISION_ENDPOINT = f"{_VISION_BASE_URL}/chat/completions"

_VISION_TIMEOUT = int(os.getenv("OPENROUTER_TIMEOUT", "60"))


def _parse_retry_after(response: "requests.Response | None") -> float | None:
    """
    Parse the Retry-After header into a wait in seconds, if present.

    Retry-After may be a non-negative integer (delta seconds) or an HTTP-date.
    Returns None when absent/unparseable so the caller (TableImageExtractor)
    falls back to its exponential backoff with jitter.
    """
    if response is None:
        return None
    raw = response.headers.get("Retry-After")
    if not raw:
        return None
    raw = raw.strip()
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        pass
    try:
        when = parsedate_to_datetime(raw)
        if when is None:
            return None
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())
    except (TypeError, ValueError, IndexError):
        return None


def _classify_status(status: int) -> tuple[str, bool]:
    """
    Map an HTTP status to (error_type, retryable) for VisionProviderError,
    per the OpenRouter-specific policy:

      429            → rate_limit, retryable
      5xx            → http_error, retryable (server/provider failure)
      other 4xx      → http_error, NOT retryable
      anything else  → http_error, NOT retryable
    """
    if status == 429:
        return VisionProviderError.ERROR_TYPE_RATE_LIMIT, True
    if 500 <= status <= 599:
        return VisionProviderError.ERROR_TYPE_HTTP, True
    return VisionProviderError.ERROR_TYPE_HTTP, False


def _strip_fences(text: str) -> str:
    """Strip a leading ```json / ``` fence and trailing ``` if present."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


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


class OpenRouterVisionProvider(VisionProvider):
    """
    VisionProvider backed by OpenRouter's OpenAI-compatible chat-completions API.

    Implements the EXISTING VisionProvider contract unchanged:
        extract_page(image_bytes, prompt) -> str   (raises VisionProviderError)

    OpenRouter multimodal request format (isolated to this class): the image is
    sent as a base64 data URL inside a user message's content array — this is
    the OpenAI-compatible shape, NOT Gemini's inline_data. Rendered pages are
    always PNG, so the data URL mime type is image/png.

    Retry ownership stays with TableImageExtractor: this provider only performs
    a single request and classifies failures into VisionProviderError. It never
    returns an empty string for a failure (an empty *successful* extraction and
    a provider failure remain distinct).

    Secrets are never logged: no API key, Authorization header, full URL with
    credentials, or request body is written to logs.
    """

    @property
    def provider_name(self) -> str:
        return f"openrouter-vision:{_VISION_MODEL}"

    def extract_page(self, image_bytes: bytes, prompt: str) -> str:
        if not _VISION_API_KEY:
            # Configuration error — not retryable.
            raise VisionProviderError(
                self.provider_name,
                "OPENROUTER_API_KEY / OPEN_ROUTER_KEY is not set",
                retryable=False,
                error_type=VisionProviderError.ERROR_TYPE_UNKNOWN,
            )

        encoded = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:image/png;base64,{encoded}"

        headers = {
            "Authorization": f"Bearer {_VISION_API_KEY}",
            "Content-Type":  "application/json",
            "X-Title":       "mflows",
        }
        payload = {
            "model": _VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
        }

        start = time.time()
        try:
            response = requests.post(
                _VISION_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=_VISION_TIMEOUT,
            )
        except requests.Timeout:
            raise VisionProviderError(
                self.provider_name,
                f"request timed out after {_VISION_TIMEOUT}s",
                retryable=True,
                error_type=VisionProviderError.ERROR_TYPE_TIMEOUT,
            )
        except Exception as exc:
            # Network/connection error — retryable per existing conventions.
            raise VisionProviderError(
                self.provider_name,
                f"network error: {exc}",
                retryable=True,
                error_type=VisionProviderError.ERROR_TYPE_UNKNOWN,
            )

        latency_ms = int((time.time() - start) * 1000)

        # ── HTTP error handling (rate limit / server / client) ────────────────
        if response.status_code >= 400:
            error_type, retryable = _classify_status(response.status_code)
            retry_after = _parse_retry_after(response) if response.status_code == 429 else None
            raise VisionProviderError(
                self.provider_name,
                f"HTTP {response.status_code}",
                retryable=retryable,
                status_code=response.status_code,
                error_type=error_type,
                retry_after=retry_after,
            )

        # ── Parse response (malformed → provider failure, never EMPTY) ────────
        try:
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            if not isinstance(text, str):
                raise ValueError("content is not a string")
        except Exception as exc:
            raise VisionProviderError(
                self.provider_name,
                f"malformed response: {exc}",
                retryable=False,
                status_code=response.status_code,
                error_type=VisionProviderError.ERROR_TYPE_HTTP,
            )

        logger.debug(
            "openrouter_vision_provider_success",
            extra={"extra_data": {
                "provider": "openrouter",
                "model": _VISION_MODEL,
                "free": _VISION_MODEL.endswith(":free"),
                "latency_ms": latency_ms,
                "result_chars": len(text),
            }},
        )
        return _strip_fences(text)
