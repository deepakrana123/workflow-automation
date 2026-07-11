from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PromptContext:
    variables: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)