"""
app/execution/executors/registry.py

ExecutorRegistry maps execution_type strings to executor instances.

Supported types are defined in ExecutionType (constants.py).
Each executor is a singleton instantiated once at class definition time.

Usage:
    executor = ExecutorRegistry.get_executor("python")
    executor.execute(configuration, context)
"""

from app.execution.executors.base_executor import BaseExecutor
from app.execution.executors.constants import ExecutionType
from app.execution.executors.http_executor import HttpExecutor
from app.execution.executors.python_executor import PythonExecutor


class ExecutorRegistry:

    _executors: dict[str, BaseExecutor] = {
        ExecutionType.PYTHON: PythonExecutor(),
        ExecutionType.HTTP:   HttpExecutor(),
    }

    @classmethod
    def get_executor(cls, execution_type: str) -> BaseExecutor:
        """
        Return the executor for the given execution_type.

        Raises:
            ValueError: if execution_type is not registered.
        """
        executor = cls._executors.get(execution_type)

        if executor is None:
            supported = ", ".join(sorted(cls._executors.keys()))
            raise ValueError(
                f"Unsupported execution_type: '{execution_type}'. "
                f"Supported types: {supported}"
            )

        return executor
