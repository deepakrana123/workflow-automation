"""
app/prompting/prompt_renderer.py

Template + Variables → Rendered Prompt.

Uses a two-pass approach to safely interpolate variable values that may
themselves contain { or } characters (workspace descriptions, rule text,
JSON examples in repair prompts, etc.):

  Pass 1 — escape any braces that already exist inside variable VALUES
            so they survive the format() call unchanged.
  Pass 2 — str.format_map() with the escaped values.

Template placeholders like {workspace_summary} work as before.
Literal {{ / }} in the template itself (for JSON examples) also work as before.
"""

import re
from app.prompting.prompt_context import PromptContext


class PromptRenderer:

    def render(self, template: str, context: PromptContext) -> str:
        """
        Render ``template`` with ``context.variables``.

        Variable values are pre-escaped so any { or } inside them do not
        interfere with Python's str.format_map().

        Raises:
            ValueError: if the template references a variable not in context.
        """
        try:
            safe_vars = {
                key: _escape_braces(str(value) if value is not None else "")
                for key, value in context.variables.items()
            }
            return template.format_map(safe_vars)
        except KeyError as exc:
            raise ValueError(f"Missing prompt variable: {exc.args[0]}") from exc


def _escape_braces(value: str) -> str:
    """
    Escape literal { and } inside a string so it survives str.format_map().

    Called on variable VALUES only — never on the template itself.
    The template uses {{ / }} for literal braces (Python convention) and
    {name} for placeholders. Variable values must not contain unescaped
    braces or they would be misinterpreted as placeholders.
    """
    return value.replace("{", "{{").replace("}", "}}")
