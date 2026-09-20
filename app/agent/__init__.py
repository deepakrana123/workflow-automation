"""
app/agent — OPT-IN agentic execution.

This package is additive and self-contained. It is NOT registered as a workflow
execution_type and does NOT alter normal DAG execution. A workflow is only ever
run "as an agent" when explicitly invoked (e.g. via a dedicated endpoint / button),
and the agent ALWAYS asks for approval before executing any action.
"""
