"""
app/prompting/prompt_manager.py

THE ONLY PUBLIC API for prompt management.

Every layer in the platform calls:
    prompt = prompt_manager.build(PromptKey.XXX, context)

Internally this resolves the template (with versioning where applicable),
renders variables, and returns the final prompt string.

No caller ever needs to know about markdown files, file paths, or versioning.
"""

from dataclasses import dataclass
from typing import Optional

from app.prompting.prompt_context import PromptContext
from app.prompting.prompt_registry import PromptKey, PromptRegistry
from app.prompting.prompt_renderer import PromptRenderer
from app.prompting.token_estimator import estimate_tokens


@dataclass(slots=True)
class PromptBuildResult:
    """
    Extended build result — useful for logging/eval pipelines
    that need version + token metadata alongside the rendered prompt.
    """

    prompt: str
    prompt_name: str
    version: str
    estimated_tokens: int


class PromptManager:
    """
    Facade that orchestrates:
        PromptRegistry (locate template) → PromptRenderer (interpolate) → result

    Usage:
        pm = PromptManager()

        # Simple — returns rendered string
        prompt = pm.build(PromptKey.WORKFLOW_EXTRACTION, context)

        # Extended — returns PromptBuildResult with metadata
        result = pm.build_with_metadata(PromptKey.WORKFLOW_GENERATION, context)
    """

    def __init__(
        self,
        registry: PromptRegistry | None = None,
        renderer: PromptRenderer | None = None,
    ):
        self._registry = registry or PromptRegistry()
        self._renderer = renderer or PromptRenderer()

    # ── Primary API ───────────────────────────────────────────────────────

    def build(
        self,
        prompt_key: PromptKey,
        context: PromptContext,
        *,
        version: Optional[str] = None,
    ) -> str:
        """
        Resolve, render, and return the final prompt string.

        Args:
            prompt_key: Which prompt to load.
            context:    Variables to interpolate.
            version:    Optional version pin (versioned prompts only).

        Returns:
            Rendered prompt string ready to send to an LLM.
        """
        template = self._registry.get(prompt_key, version=version)
        return self._renderer.render(template, context)

    # ── Extended API (for pipelines that need metadata) ───────────────────

    def build_with_metadata(
        self,
        prompt_key: PromptKey,
        context: PromptContext,
        *,
        version: Optional[str] = None,
    ) -> PromptBuildResult:
        """
        Same as build(), but returns a PromptBuildResult containing
        the rendered prompt plus version and token metadata.

        Useful for eval logging, auto-rollback tracking, etc.
        """
        template = self._registry.get(prompt_key, version=version)
        rendered = self._renderer.render(template, context)

        version_info = self._registry.get_version_info(prompt_key)

        return PromptBuildResult(
            prompt=rendered,
            prompt_name=prompt_key.value,
            version=version_info["version"],
            estimated_tokens=estimate_tokens(rendered),
        )
