"""
app/prompting/prompt_context.py

Generic container for prompt variables and metadata.
No business knowledge — just a bag of values to interpolate.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PromptContext:
    """
    Carries variables that will be interpolated into a prompt template,
    plus optional metadata (prompt_name override, version pin, etc.).

    Usage:
        ctx = PromptContext(variables={"text": doc, "schema": schema})
        ctx = PromptContext(
            variables={"user_request": req},
            metadata={"version": "v2"},
        )
    """

    variables: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
