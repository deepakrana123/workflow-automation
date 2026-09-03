"""
app/knowledge_ingestions/providers/gemini.py

Gemini implementations of VisionProvider and TextProvider.

GeminiVisionProvider  — sends image bytes + prompt to Gemini via inline_data.
GeminiTextProvider    — sends a text-only prompt to Gemini.

Both reuse the same model and API key already configured for the rest of the
system (GEMINI_API_KEY, GEMINI_MODEL env vars in gemini_rest.py).

Why separate classes instead of one combined class:
  The interfaces are separate. A future model might support vision but not
  text generation, or vice versa. Keeping them separate means the registry
  can wire a vision-capable model for image pages and a cheaper text-only
  model for appendix extraction independently.

Why inline_data over file upload API:
  Gemini's File API requires an upload step, a file ID, and cleanup.
  inline_data is one request, no state, no cleanup, simpler error handling.
  For BRD page images (typically < 1MB each) inline_data is the right choice.
  If pages exceed 4MB, switch to the File API — that change is isolated here.
"""

import base64
import os
import time

import requests
from dotenv import load_dotenv

from app.core.logger import logger
from app.knowledge_ingestions.providers.base import (
    VisionProvider,
    TextProvider,
    VisionProviderError,
    TextProviderError,
)

load_dotenv()

_API_KEY = os.getenv("GEMINI_API_KEY")
_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "30"))

_BASE_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/{_MODEL}:generateContent?key={_API_KEY}"
)


def _post(payload: dict) -> str:
    """
    Shared POST helper — makes the HTTP call and extracts the text response.

    Returns the model's text output as a string.
    Raises requests.HTTPError / requests.Timeout on transport failures.
    """
    start = time.time()
    response = requests.post(_BASE_URL, json=payload, timeout=_TIMEOUT)
    response.raise_for_status()
    data    = response.json()
    text    = data["candidates"][0]["content"]["parts"][0]["text"]
    latency = int((time.time() - start) * 1000)
    logger.debug(
        "gemini_provider_call_success",
        extra={"extra_data": {"latency_ms": latency}},
    )
    # Strip markdown fences if the model wraps output in them
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


class GeminiVisionProvider(VisionProvider):
    """
    Vision extraction using Gemini's inline_data multimodal API.

    Each call sends one page image alongside the extraction prompt.
    The model returns structured text describing what it sees on the page.

    Supported image formats: PNG, JPEG, WEBP, HEIC, HEIF.
    We always render to PNG via pdf2image so mime_type is always image/png.
    """

    @property
    def provider_name(self) -> str:
        return f"gemini-vision:{_MODEL}"

    def extract_page(self, image_bytes: bytes, prompt: str) -> str:
        """
        Send one rendered page image to Gemini and return extracted content.

        Args:
            image_bytes: raw PNG bytes of the rendered PDF page
            prompt:      extraction instruction (table prompt or image prompt)

        Returns:
            Extracted content as plain text or JSON string.

        Raises:
            VisionProviderError on any failure.
        """
        encoded = base64.b64encode(image_bytes).decode("utf-8")

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data":      encoded,
                        }
                    },
                ]
            }]
        }

        try:
            return _post(payload)
        except requests.Timeout:
            raise VisionProviderError(
                self.provider_name,
                f"request timed out after {_TIMEOUT}s",
                retryable=True,
            )
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 0
            retryable = status not in (401, 403)
            raise VisionProviderError(
                self.provider_name,
                f"HTTP {status}: {exc}",
                retryable=retryable,
            )
        except Exception as exc:
            raise VisionProviderError(
                self.provider_name,
                str(exc),
                retryable=True,
            )


class GeminiTextProvider(TextProvider):
    """
    Text-only generation using Gemini.

    Used for appendix extraction where the content is already plain text
    and no image rendering is needed.

    This is functionally equivalent to try_call_gemini_rest() but conforms
    to the TextProvider interface so it can be swapped for any other model.
    """

    @property
    def provider_name(self) -> str:
        return f"gemini-text:{_MODEL}"

    def generate(self, prompt: str) -> str:
        """
        Generate a response for a text-only prompt.

        Returns:
            Model response as a plain string.

        Raises:
            TextProviderError on any failure.
        """
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        try:
            return _post(payload)
        except requests.Timeout:
            raise TextProviderError(
                self.provider_name,
                f"request timed out after {_TIMEOUT}s",
                retryable=True,
            )
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 0
            retryable = status not in (401, 403)
            raise TextProviderError(
                self.provider_name,
                f"HTTP {status}: {exc}",
                retryable=retryable,
            )
        except Exception as exc:
            raise TextProviderError(
                self.provider_name,
                str(exc),
                retryable=True,
            )
