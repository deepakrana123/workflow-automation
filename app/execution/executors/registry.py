"""
app/execution/executors/registry.py

ExecutorRegistry — maps execution_type strings to executor instances.

Supported types: python, http.
Raise ExecutorNotFoundError for anything else.
"""

from app.execution.executors.base_executor import BaseExecutor
from app.execution.executors.constants import ExecutionType
from app.execution.executors.http_executor import HttpExecutor
from app.execution.executors.python_executor import PythonExecutor
from app.execution.exceptions import ExecutorNotFoundError


class ExecutorRegistry:

    def __init__(
        self,
        executors: dict[str, BaseExecutor] | None = None,
    ):
        self._executors = executors or {
            ExecutionType.PYTHON: PythonExecutor(),
            ExecutionType.HTTP:   HttpExecutor(),
        }

    def get_executor(self, execution_type: str) -> BaseExecutor:
        executor = self._executors.get(execution_type)
        if executor is None:
            raise ExecutorNotFoundError(
                execution_type=execution_type,
                supported=list(self._executors.keys()),
            )
        return executor


# Default singleton instance — preserves existing behavior for callers
# that use ExecutorRegistry.get_executor() as a classmethod-style call.
_default_registry = ExecutorRegistry()


def get_executor(execution_type: str) -> BaseExecutor:
    """Module-level convenience — same behavior as the old classmethod."""
    return _default_registry.get_executor(execution_type)
