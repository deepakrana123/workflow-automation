"""
DEPRECATED: Moved to app.prompting.prompt_manager

This shim exists for backward compatibility. Import from app.prompting instead.
"""
from app.prompting.prompt_version import PromptVersion  # noqa: F401

# Typo-compat alias
PropmptVersion = PromptVersion


class PromptService:
    """DEPRECATED: Use PromptManager from app.prompting instead."""

    def __init__(self, registry=None):
        from app.prompting import PromptManager
        self._pm = PromptManager()

    def build(self, context):
        from app.prompting import PromptContext, PromptKey
        new_ctx = PromptContext(variables={
            "workflow_type": context.workflow_type or "general",
            "triggers": "\n".join(context.triggers),
            "actions": "\n".join(context.actions),
            "user_request": context.user_request,
        })
        result = self._pm.build_with_metadata(PromptKey.WORKFLOW_GENERATION, new_ctx)
        return result.prompt
