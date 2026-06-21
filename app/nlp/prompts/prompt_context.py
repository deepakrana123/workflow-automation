from dataclasses import dataclass, field


@dataclass
class PromptContext:
    workflow_type: str | None
    triggers: list[str]
    actions: list[str]
    user_request: str
    semantic_triggers: list[dict] = field(default_factory=list)
    semantic_actions: list[dict] = field(default_factory=list)
