"""
app/prompting/prompt_renderer.py

Template + Variables → Rendered Prompt.

Validates that all required variables are present and raises
clear errors when they are missing.
"""

from app.prompting.prompt_context import PromptContext


class PromptRenderer:
    def render(self, template: str, context: PromptContext) -> str:
        try:
            return template.format(**context.variables)
        except KeyError as exc:
            raise ValueError(f"Missing prompt variable: {exc.args[0]}") from exc
