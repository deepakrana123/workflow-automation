"""
app/execution/executors/constants.py

Execution type identifiers used by ExecutorRegistry to route actions.
Only types with registered executor implementations are listed here.
"""


class ExecutionType:
    PYTHON = "python"
    HTTP = "http"
    HUMAN_TASK = "human_task"
    # Future: uncomment when executor implementations are added
    # MCP = "mcp"
    # KAFKA = "kafka"


# Marker placed on ActionResult.metadata by executors that suspend the DAG
# (e.g. HumanExecutor). The step executor detects this and halts the step in
# a WAITING state instead of completing or failing it.
EXECUTION_STATUS_WAITING = "WAITING"
