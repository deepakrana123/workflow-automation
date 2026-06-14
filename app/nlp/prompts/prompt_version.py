from dataclasses import dataclass


@dataclass
class PromptVersion:
    """
    Represents a single versioned prompt template.

    Attributes:
        name:     Prompt identifier, e.g. "workflow_generation"
        version:  Version string, e.g. "v1", "v2"
        template: Full template text loaded from disk
    """
    name: str
    version: str
    template: str
