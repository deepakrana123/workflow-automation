"""
app/execution/executors/constants.py

Execution type identifiers used by ExecutorRegistry to route actions.
Only types with registered executor implementations are listed here.
"""


class ExecutionType:
    PYTHON = "python"
    HTTP = "http"
    # Future: uncomment when executor implementations are added
    # HUMAN_TASK = "human_task"
    # MCP = "mcp"
    # KAFKA = "kafka"
