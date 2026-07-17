"""
DEPRECATED: Moved to app.prompting.prompt_version

This shim exists for backward compatibility. Import from app.prompting instead.
"""
from app.prompting.prompt_version import PromptVersion  # noqa: F401

# Typo-compat alias (was in original code)
PropmptVersion = PromptVersion
