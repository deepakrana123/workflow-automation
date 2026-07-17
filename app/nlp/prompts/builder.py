"""
DEPRECATED: Moved to app.prompting.prompt_manager

This shim exists for backward compatibility. Import from app.prompting instead.

    from app.prompting import PromptManager, PromptBuildResult
"""
from app.prompting.prompt_manager import PromptBuildResult  # noqa: F401

# Legacy constant kept for scripts that reference it
PROMPT_NAME = "workflow_generation"


class PromptBuilder:
    """
    DEPRECATED: Use PromptManager instead.

    Thin wrapper that delegates to the unified PromptManager
    so old callers continue to work without changes.
    """

    def __init__(self):
        from app.prompting import PromptManager, PromptKey
        self._pm = PromptManager()
        self._key = PromptKey.WORKFLOW_GENERATION

    def build(self, context) -> PromptBuildResult:
        from app.prompting import PromptContext as NewContext

        # Adapt old-style PromptContext (with typed fields) to new generic one
        if hasattr(context, "variables"):
            new_ctx = context
        else:
            new_ctx = NewContext(variables={
                "workflow_type": context.workflow_type or "general",
                "triggers": "\n".join(context.triggers),
                "actions": "\n".join(context.actions),
                "user_request": context.user_request,
            })

        return self._pm.build_with_metadata(self._key, new_ctx)
