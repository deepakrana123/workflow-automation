from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class GeneratedFile:
    file_name: str

    mime_type: str

    content: bytes

    extension: str

    size: int

    metadata: dict[str, Any] = field(default_factory=dict)

    generated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )