"""
app/prompts/__init__.py

Prompt template files (.md) live in this directory.

Use the PromptManager API for all new code:

    from app.prompting import PromptManager, PromptContext, PromptKey

    pm = PromptManager()
    prompt = pm.build(PromptKey.WORKFLOW_EXTRACTION, PromptContext(variables={...}))
"""
