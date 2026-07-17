"""
app/prompts/__init__.py

Prompt template files live in this directory as .md files.

DEPRECATED: Importing prompt constants from this module is deprecated.
Use the PromptManager API instead:

    from app.prompting import PromptManager, PromptContext, PromptKey

    pm = PromptManager()
    prompt = pm.build(PromptKey.WORKFLOW_EXTRACTION, PromptContext(variables={...}))

The module-level constants below are kept temporarily for backward compatibility.
"""

from pathlib import Path

_DIR = Path(__file__).parent


def _load(filename: str) -> str:
    """Read a prompt .md file and return its content as a string."""
    return (_DIR / filename).read_text(encoding="utf-8")


# Backward-compatible constant — prefer PromptManager.build() in new code
WORKFLOW_EXTRACTION_PROMPT: str = _load("extractor.md")
