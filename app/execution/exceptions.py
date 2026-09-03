"""
app/execution/exceptions.py

Execution layer exception hierarchy.
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


class HandlerNotFoundError(ExecutionError):
    """Raised when action_name has no match in ActionHandlerRegistry or global catalog."""

    def __init__(self, handler_name: str | None, action_configuration_id: int | None):
        msg = (
            f"Handler '{handler_name}' not found in ActionHandlerRegistry"
            if handler_name
            else "No handler defined for action"
        )
        super().__init__(msg)
        self.handler_name = handler_name
        self.action_configuration_id = action_configuration_id


class ExternalExecutionError(ExecutionError):
    """Raised by HttpExecutor on network, timeout, or non-2xx HTTP errors."""

    def __init__(self, message: str, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable
