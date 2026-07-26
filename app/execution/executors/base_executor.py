from abc import ABC, abstractmethod

from app.models.action_configurations_model import ActionConfiguration
from app.workflow_execution.schemas.action_result import ActionResult


class BaseExecutor(ABC):
    """
    Abstract base for all execution type implementations.

    Each executor receives an ActionConfiguration and the current
    step payload (context) and returns an ActionResult.
    """

    @abstractmethod
    def execute(
        self,
        configuration: ActionConfiguration,
        context: dict,
    ) -> ActionResult:
        ...
