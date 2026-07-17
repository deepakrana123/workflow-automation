"""
app/prompting/prompt_renderer.py

Template + Variables → Rendered Prompt.

Validates that all required variables are present and raises
clear errors when they are missing.
"""

from app.prompting.prompt_context import PromptContext


class PromptRenderer:
    """
    Renders a prompt template by interpolating variables from a PromptContext.

    Uses Python str.format() — templates use {placeholder} syntax.
    """

    def render(self, template: str, context: PromptContext) -> str:
        """
        Render the template with the given context variables.

        Args:
            template: Raw template string with {placeholder} markers.
            context:  PromptContext carrying the variables dict.

        Returns:
            Fully rendered prompt string.

        Raises:
            ValueError: If a required placeholder has no matching variable.
        """
        try:
            return template.format(**context.variables)
        except KeyError as exc:
            available = sorted(context.variables.keys())
            raise ValueError(
                f"Missing prompt variable: '{exc.args[0]}'. "
                f"Available variables: {available}"
            ) from exc
