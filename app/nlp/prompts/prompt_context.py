from dataclasses import dataclass
@dataclass
class PromptContext:

    workflow_type: str | None

    triggers: list[str]

    actions: list[str]

    user_request: str