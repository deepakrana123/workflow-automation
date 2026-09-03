from abc import ABC, abstractmethod

from app.models.action_definitions import ActionDefinition
from app.workflow_execution.schemas.action_result import ActionResult


class BaseExecutor(ABC):
    """
    Abstract base for all execution type implementations.

    Each executor receives the resolved ActionDefinition and the current
    step payload (context) and returns an ActionResult.
    """

    @abstractmethod
    def execute(
        self,
        action_definition: ActionDefinition,
        context: dict,
    ) -> ActionResult:
        ...
