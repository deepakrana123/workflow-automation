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
    """Raised by a VisionProvider on unrecoverable failure."""

    def __init__(self, provider: str, message: str, retryable: bool = True):
        super().__init__(f"[{provider}] {message}")
        self.provider  = provider
        self.retryable = retryable


class TextProviderError(Exception):
    """Raised by a TextProvider on unrecoverable failure."""

    def __init__(self, provider: str, message: str, retryable: bool = True):
        super().__init__(f"[{provider}] {message}")
        self.provider  = provider
        self.retryable = retryable
