from app.nlp.prompts.prompt_version import PropmptVersion


class PromptService:
    def __init__(self):
        self.active_prompt = PropmptVersion(version="v1", template="")

    def build(self, context):
        return self.active_prompt.template.format(
            workflow_type=context.workflow_type,
            triggers="\n".join(context.triggers),
            actions="\n".join(context.actions),
            user_request=context.user_request,
        )
