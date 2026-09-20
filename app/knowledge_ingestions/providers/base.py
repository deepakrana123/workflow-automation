"""
app/knowledge_ingestions/providers/base.py

Abstract provider contracts for the multimodal BRD extraction pipeline.

Two interfaces:

  VisionProvider — accepts an image (bytes) + a text prompt and returns
                   the model's text response. Used for table pages,
                   diagram pages, and scanned pages.

  TextProvider   — accepts a text prompt and returns the model's text
                   response. Used for appendix extraction and any
                   text-only supplementary pass.

Why abstract classes instead of protocols:
  ABCs enforce the contract at class definition time (raises TypeError on
  instantiation if abstract methods are not implemented). Protocols would
  only be caught at type-check time. For provider swapping in production
  we want a hard runtime failure if someone wires in a half-implemented
  provider, not a silent AttributeError later.

Adding a new model:
  1. Create app/knowledge_ingestions/providers/<model_name>.py
  2. Implement VisionProvider and/or TextProvider
  3. Register it in ProviderRegistry (providers/registry.py)
  4. Set the env var VISION_PROVIDER=<name> or TEXT_PROVIDER=<name>
  Nothing else needs to change.
"""

from abc import ABC, abstractmethod


class VisionProvider(ABC):
    """
    Sends an image + prompt to a vision-capable model and returns
    the model's text response.

    Contract:
      - image_bytes: raw PNG/JPEG bytes of the rendered page
      - prompt:      instruction telling the model what to extract
      - returns:     extracted text/structured content as a plain string
      - raises:      VisionProviderError on unrecoverable failure
    """

    @abstractmethod
    def extract_page(self, image_bytes: bytes, prompt: str) -> str:
        """
        Process one page image and return extracted content as a string.

        The string may be plain text, JSON, or markdown — the caller
        decides how to interpret it based on the prompt it sent.
        """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name used in logs and diagnostics."""


class TextProvider(ABC):
    """
    Sends a text-only prompt to a language model and returns the
    model's text response.

    Contract:
      - prompt:   the full text prompt
      - returns:  model response as a plain string
      - raises:   TextProviderError on unrecoverable failure
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Generate a text response from a text-only prompt.
        """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name used in logs and diagnostics."""


# ── Provider-specific exceptions ──────────────────────────────────────────────

class VisionProviderError(Exception):
    """
    Raised by a VisionProvider on unrecoverable failure.

    Carries enough structured detail for the caller to distinguish a
    rate-limit (HTTP 429) from a generic provider failure and to honour a
    server-provided Retry-After. All new fields are optional and default to
    None, so existing call sites — ``VisionProviderError(name, msg,
    retryable=...)`` — keep working unchanged.

    Fields:
        provider     human-readable provider name (e.g. "gemini-vision:...")
        retryable    whether a retry could plausibly succeed
        status_code  HTTP status code when the failure was an HTTP error
        error_type   coarse classification — one of the _ERROR_TYPE_* strings
                     below ("rate_limit", "timeout", "http_error", "unknown")
        retry_after  server-requested wait in seconds (parsed from the
                     Retry-After header), when provided
    """

    # Coarse error-type vocabulary (kept as plain strings for log/JSON use).
    ERROR_TYPE_RATE_LIMIT = "rate_limit"
    ERROR_TYPE_TIMEOUT     = "timeout"
    ERROR_TYPE_HTTP        = "http_error"
    ERROR_TYPE_UNKNOWN     = "unknown"

    def __init__(
        self,
        provider: str,
        message: str,
        retryable: bool = True,
        *,
        status_code: int | None = None,
        error_type: str | None = None,
        retry_after: float | None = None,
    ):
        super().__init__(f"[{provider}] {message}")
        self.provider     = provider
        self.retryable    = retryable
        self.status_code  = status_code
        self.error_type   = error_type
        self.retry_after  = retry_after

    @property
    def is_rate_limited(self) -> bool:
        """True when this failure is specifically a rate-limit (HTTP 429)."""
        return self.status_code == 429 or self.error_type == self.ERROR_TYPE_RATE_LIMIT


class TextProviderError(Exception):
    """Raised by a TextProvider on unrecoverable failure."""

    def __init__(self, provider: str, message: str, retryable: bool = True):
        super().__init__(f"[{provider}] {message}")
        self.provider  = provider
        self.retryable = retryable
