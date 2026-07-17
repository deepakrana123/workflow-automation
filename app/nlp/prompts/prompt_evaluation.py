"""
DEPRECATED: Moved to app.prompting.prompt_evaluation

This shim exists for backward compatibility. Import from app.prompting instead.
"""
from app.prompting.prompt_evaluation import PromptEvaluation  # noqa: F401

# Typo-compat alias (was in original code)
PromptEvalution = PromptEvaluation
