from dataclasses import dataclass


@dataclass
class PromptEvalution:
    prompt_version: str
    success: bool
    latency_ms: int
    provider: str
