"""
app/nlp/prompts/builder.py

Builds the final prompt string from a PromptContext.

Uses the active version from PromptVersionStore.
Returns a PromptBuildResult with the prompt text, version used,
and estimated token count — so callers can log all three.
"""

from dataclasses import dataclass
from app.nlp.prompts.prompt_context import PromptContext
from app.nlp.prompts.prompt_registry import registry
from app.nlp.prompts.prompt_version_store import version_store
from app.nlp.prompts.token_estimator import estimate_tokens

PROMPT_NAME = "workflow_generation"


@dataclass
class PromptBuildResult:
    prompt: str
    prompt_name: str
    version: str
    estimated_tokens: int


class PromptBuilder:

    def build(self, context: PromptContext) -> PromptBuildResult:
        """
        Build the final prompt for the given context.

        Reads the active version from PromptVersionStore,
        loads the template from PromptRegistry,
        interpolates context fields,
        estimates token count.

        Returns PromptBuildResult — never a bare string.
        """
        version = version_store.get_active(PROMPT_NAME)
        prompt_version = registry.get(PROMPT_NAME, version)

        trigger_block = "\n".join(context.triggers)
        action_block = "\n".join(context.actions)

        prompt = prompt_version.template.format(
            workflow_type=context.workflow_type or "general",
            triggers=trigger_block,
            actions=action_block,
            user_request=context.user_request,
        )

        return PromptBuildResult(
            prompt=prompt,
            prompt_name=PROMPT_NAME,
            version=version,
            estimated_tokens=estimate_tokens(prompt),
        )
