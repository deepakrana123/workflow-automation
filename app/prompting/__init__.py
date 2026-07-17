"""
app/prompting — Unified prompt management layer.

Public API:
    from app.prompting import PromptManager, PromptContext, PromptKey

    pm = PromptManager()
    prompt = pm.build(PromptKey.WORKFLOW_EXTRACTION, PromptContext(variables={...}))
"""

from app.prompting.prompt_context import PromptContext
from app.prompting.prompt_manager import PromptManager, PromptBuildResult
from app.prompting.prompt_registry import PromptKey, PromptRegistry
from app.prompting.prompt_version_store import version_store
from app.prompting.token_estimator import estimate_tokens

__all__ = [
    "PromptContext",
    "PromptKey",
    "PromptManager",
    "PromptBuildResult",
    "PromptRegistry",
    "version_store",
    "estimate_tokens",
]
