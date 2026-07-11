from app.prompting.prompt_context import PromptContext
from app.prompting.prompt_registry import PromptKey, PromptRegistry
from app.prompting.prompt_renderer import PromptRenderer


class PromptManager:
    def __init__(
        self,
        registry: PromptRegistry | None = None,
        renderer: PromptRenderer | None = None,
    ):
        self._registry = registry or PromptRegistry()
        self._renderer = renderer or PromptRenderer()

    def build(
        self,
        prompt_key: PromptKey,
        context: PromptContext,
    ) -> str:
        template = self._registry.get(prompt_key)
        return self._renderer.render(template, context)