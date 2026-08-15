"""
app/execution/exceptions.py

Execution layer exception hierarchy.

All exceptions raised inside executors, the registry, and the step executor
inherit from ExecutionError so callers can catch the base class when needed.
"""


class ExecutionError(Exception):
    """Base class for all execution layer errors."""


class ExecutorNotFoundError(ExecutionError):
    """Raised when ExecutorRegistry has no executor for the given execution_type."""

    def __init__(self, execution_type: str, supported: list[str]):
        super().__init__(
            f"No executor registered for execution_type='{execution_type}'. "
            f"Supported: {', '.join(sorted(supported))}"
        )
        self.execution_type = execution_type
        self.supported = supported


class ConfigurationNotFoundError(ExecutionError):
    """Raised when no ActionConfiguration can be resolved for an action."""

    def __init__(self, action_name: str, workflow_knowledge_id: int | None):
        super().__init__(
            f"No ActionConfiguration found for action='{action_name}' "
            f"(workflow_knowledge_id={workflow_knowledge_id})"
        )
        self.action_name = action_name
        self.workflow_knowledge_id = workflow_knowledge_id


class HandlerNotFoundError(ExecutionError):
    """Raised by PythonExecutor when handler_name is missing or not in the registry."""

    def __init__(self, handler_name: str | None, action_configuration_id: int | None):
        msg = (
            f"Handler '{handler_name}' not found in ActionHandlerRegistry"
            if handler_name
            else "No handler defined in ActionConfiguration.configuration"
        )
        super().__init__(msg)
        self.handler_name = handler_name
        self.action_configuration_id = action_configuration_id


class ExternalExecutionError(ExecutionError):
    """Raised by HttpExecutor on network, timeout, or non-2xx HTTP errors."""

    def __init__(self, message: str, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable
