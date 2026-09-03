"""
app/knowledge_ingestions/providers/registry.py

ProviderRegistry — resolves VisionProvider and TextProvider implementations
from environment variables so the rest of the pipeline never imports a
specific provider directly.

Environment variables:
  VISION_PROVIDER   name of the vision provider to use (default: gemini)
  TEXT_PROVIDER     name of the text provider to use   (default: gemini)

Adding a new model requires only two steps:
  1. Implement VisionProvider / TextProvider in a new file under providers/
  2. Add an entry to _VISION_PROVIDERS or _TEXT_PROVIDERS below
  3. Set the env var — nothing else changes

Why a registry dict instead of importlib / plugin system:
  Explicit is better than implicit. The registry is the single place where
  model names map to classes. Anyone reading the code can see exactly what
  models are available without scanning the filesystem. A plugin system
  would be warranted if external teams needed to add models without modifying
  this file — that is not the current requirement.

Why lazy instantiation (lambda):
  Providers may import heavy dependencies (requests, base64, etc.) at module
  level. We only import and instantiate the one provider that is actually
  configured, not all of them. This keeps startup fast and avoids import
  errors for providers whose dependencies are not installed.
"""

import os
from typing import Callable

from app.knowledge_ingestions.providers.base import VisionProvider, TextProvider


# ── Registry tables ───────────────────────────────────────────────────────────
# Each entry is a zero-argument factory that returns a fresh provider instance.
# Using factories (lambdas) instead of singletons so each extraction job can
# get its own instance — no shared mutable state between concurrent requests.

_VISION_PROVIDERS: dict[str, Callable[[], VisionProvider]] = {
    "gemini": lambda: _import_gemini().GeminiVisionProvider(),
    # Future:
    # "openai":  lambda: _import_openai().OpenAIVisionProvider(),
    # "claude":  lambda: _import_claude().ClaudeVisionProvider(),
    # "llava":   lambda: _import_llava().LLaVAVisionProvider(),
}

_TEXT_PROVIDERS: dict[str, Callable[[], TextProvider]] = {
    "gemini": lambda: _import_gemini().GeminiTextProvider(),
    # Future:
    # "openai":  lambda: _import_openai().OpenAITextProvider(),
    # "claude":  lambda: _import_claude().ClaudeTextProvider(),
    # "ollama":  lambda: _import_ollama().OllamaTextProvider(),
}


# ── Public API ────────────────────────────────────────────────────────────────

def get_vision_provider() -> VisionProvider:
    """
    Return a configured VisionProvider based on the VISION_PROVIDER env var.

    Default: gemini

    Raises:
        ValueError: if the env var names an unregistered provider.
    """
    name = os.getenv("VISION_PROVIDER", "gemini").lower().strip()
    factory = _VISION_PROVIDERS.get(name)
    if factory is None:
        available = sorted(_VISION_PROVIDERS.keys())
        raise ValueError(
            f"Unknown VISION_PROVIDER='{name}'. "
            f"Available: {available}"
        )
    return factory()


def get_text_provider() -> TextProvider:
    """
    Return a configured TextProvider based on the TEXT_PROVIDER env var.

    Default: gemini

    Raises:
        ValueError: if the env var names an unregistered provider.
    """
    name = os.getenv("TEXT_PROVIDER", "gemini").lower().strip()
    factory = _TEXT_PROVIDERS.get(name)
    if factory is None:
        available = sorted(_TEXT_PROVIDERS.keys())
        raise ValueError(
            f"Unknown TEXT_PROVIDER='{name}'. "
            f"Available: {available}"
        )
    return factory()


def available_vision_providers() -> list[str]:
    """Return list of registered vision provider names."""
    return sorted(_VISION_PROVIDERS.keys())


def available_text_providers() -> list[str]:
    """Return list of registered text provider names."""
    return sorted(_TEXT_PROVIDERS.keys())


# ── Lazy imports ──────────────────────────────────────────────────────────────

def _import_gemini():
    from app.knowledge_ingestions.providers import gemini as _gemini
    return _gemini
