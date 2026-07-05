from typing import Any


class WorkflowContext:
    """Carries accumulated outputs across workflow steps."""

    def __init__(self, entity_id: str | None = None):
        self.entity_id = entity_id
        self.outputs: dict[str, Any] = {}

    def update(self, result_outputs: dict[str, Any]) -> None:
        self.outputs.update(result_outputs)

    def to_payload(self) -> dict[str, Any]:
        return {"entity_id": self.entity_id, **self.outputs}
