from app.prompting.prompt_context import PromptContext


class PromptRenderer:
    def render(self, template: str, context: PromptContext) -> str:
        try:
            return template.format(**context.variables)
        except KeyError as exc:
            raise ValueError(f"Missing prompt variable: {exc.args[0]}") from exc
