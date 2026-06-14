from app.nlp.prompts.prompt_version import PropmptVersion
from pathlib import Path


class PromptService:
    def __init__(self, registry):
        self.registry = registry

    def build(self, context):
        prompt = self.registry.latest()
        return prompt.template.format(
            workflow_type=context.workflow_type,
            triggers="\n".join(context.triggers),
            actions="\n".join(context.actions),
            user_request=context.user_request,
        )
