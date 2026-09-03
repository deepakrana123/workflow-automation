"""
app/prompting/prompt_registry.py

Unified prompt registry.

Responsibilities:
- Locates prompt templates on disk (markdown or txt).
- Integrates with PromptVersionStore for versioned prompts.
- Returns the raw template string — never formats it.

Supports two resolution strategies:
1. Versioned prompts  — stored under  app/prompting/versions/{prompt_name}/v1.txt
2. Flat prompts       — stored under  app/prompts/{filename}.md

PromptKey declares which strategy each prompt uses.
"""

from enum import Enum
from pathlib import Path
from typing import Optional

from app.prompting.versioned_registry import versioned_registry
from app.prompting.prompt_version_store import version_store


# ─── Prompt directory roots ──────────────────────────────────────────────────

_FLAT_PROMPT_ROOT = Path(__file__).parent.parent / "prompts"


# ─── Prompt keys ─────────────────────────────────────────────────────────────

class PromptKey(str, Enum):
    """
    Each key maps to a prompt template location.

    Convention:
      - Keys ending with .md  → resolved as flat files under app/prompts/
      - Keys without extension → resolved as versioned prompts via VersionedPromptRegistry
    """

    # Flat (markdown) prompts
    WORKFLOW_EXTRACTION = "extractor.md"

    # Versioned prompts (name matches directory under versions/)
    WORKFLOW_GENERATION = "workflow_generation"

    @property
    def is_versioned(self) -> bool:
        """True if this key resolves through the version store."""
        return not self.value.endswith(".md")


# ─── Registry ────────────────────────────────────────────────────────────────

class PromptRegistry:
    """
    Single entry point for loading prompt templates.

    Delegates:
      - Versioned prompts → app.prompting.versioned_registry
      - Flat prompts      → direct file read from app/prompts/
    """

    def __init__(
        self,
        flat_root: Path | None = None,
    ):
        self._flat_root = flat_root or _FLAT_PROMPT_ROOT

    # ── Public API ────────────────────────────────────────────────────────

    def get(self, key: PromptKey, version: Optional[str] = None) -> str:
        """
        Load and return the raw template text for the given prompt key.

        Args:
            key:     Prompt identifier.
            version: Explicit version override (versioned prompts only).
                     If None, the active version from PromptVersionStore is used.

        Returns:
            Template string ready for rendering.

        Raises:
            FileNotFoundError: Flat prompt file does not exist.
            KeyError:          Versioned prompt or requested version not found.
        """
        if key.is_versioned:
            return self._resolve_versioned(key, version)
        return self._resolve_flat(key)

    def get_version_info(self, key: PromptKey) -> dict:
        """
        Return version metadata for a versioned prompt.
        For flat prompts returns {"version": "latest"}.
        """
        if key.is_versioned:
            active = version_store.get_active(key.value)
            return {
                "prompt_name": key.value,
                "version": active,
                "available": versioned_registry.list_versions(key.value),
            }
        return {"prompt_name": key.value, "version": "latest"}

    def list_prompts(self) -> list[str]:
        """Return all known prompt names (versioned)."""
        return versioned_registry.list_prompts()

    def list_versions(self, prompt_name: str) -> list[str]:
        """Return all available versions for a prompt."""
        return versioned_registry.list_versions(prompt_name)

    # ── Private resolution ────────────────────────────────────────────────

    def _resolve_flat(self, key: PromptKey) -> str:
        path = self._flat_root / key.value
        if not path.exists():
            raise FileNotFoundError(
                f"Prompt template not found: {path}"
            )
        return path.read_text(encoding="utf-8")

    def _resolve_versioned(self, key: PromptKey, version: Optional[str]) -> str:
        prompt_name = key.value
        resolved_version = version or version_store.get_active(prompt_name)
        prompt_version = versioned_registry.get(prompt_name, resolved_version)
        return prompt_version.template
