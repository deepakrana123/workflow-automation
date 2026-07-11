class PromptRenderer:

    def render(
        self,
        template: str,
        **variables,
    ) -> str:
        return template.format(**variables)