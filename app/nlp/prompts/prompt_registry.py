"""
app/nlp/prompts/prompt_registry.py

File-based prompt registry.
Discovers all versions for a prompt_name by scanning the versions/ directory.
Loads and caches templates at startup.

Directory layout:
    app/nlp/prompts/versions/
        workflow_generation/
            v1.txt
            v2.txt   ← future
"""

from pathlib import Path
from app.nlp.prompts.prompt_version import PromptVersion

_VERSIONS_DIR = Path(__file__).parent / "versions"


class PromptRegistry:
    """
    Loads all available versions for every prompt_name found under versions/.
    Provides access by name + version.
    """

    def __init__(self):
        # { prompt_name: { version_str: PromptVersion } }
        self._registry: dict[str, dict[str, PromptVersion]] = {}
        self._load_all()

    def _load_all(self) -> None:
        if not _VERSIONS_DIR.exists():
            return
        for prompt_dir in sorted(_VERSIONS_DIR.iterdir()):
            if not prompt_dir.is_dir():
                continue
            prompt_name = prompt_dir.name
            self._registry[prompt_name] = {}
            for version_file in sorted(prompt_dir.glob("*.txt")):
                version = version_file.stem          # "v1", "v2", ...
                template = version_file.read_text(encoding="utf-8")
                self._registry[prompt_name][version] = PromptVersion(
                    name=prompt_name,
                    version=version,
                    template=template,
                )

    def get(self, prompt_name: str, version: str) -> PromptVersion:
        """
        Retrieve a specific version of a prompt.
        Raises KeyError if prompt_name or version is not found.
        """
        if prompt_name not in self._registry:
            raise KeyError(f"Unknown prompt: '{prompt_name}'")
        versions = self._registry[prompt_name]
        if version not in versions:
            raise KeyError(
                f"Version '{version}' not found for prompt '{prompt_name}'. "
                f"Available: {sorted(versions.keys())}"
            )
        return versions[version]

    def list_versions(self, prompt_name: str) -> list[str]:
        """Return all available version strings for a prompt_name."""
        return sorted(self._registry.get(prompt_name, {}).keys())

    def list_prompts(self) -> list[str]:
        """Return all known prompt names."""
        return sorted(self._registry.keys())


# Module-level singleton — loaded once at import time
registry = PromptRegistry()
