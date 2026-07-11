"""
app/prompts/__init__.py

Loads prompt templates from .md files in this directory.

Each prompt is exposed as a plain string ready for .format() calls.
The .md files use {placeholder} syntax for variable substitution.
"""

from pathlib import Path

_DIR = Path(__file__).parent


def _load(filename: str) -> str:
    """Read a prompt .md file and return its content as a string."""
    return (_DIR / filename).read_text(encoding="utf-8")


WORKFLOW_EXTRACTION_PROMPT: str = _load("extractor.md")
