"""Unit tests for the Human Executor and the DAG scheduler's waiting logic."""

from types import SimpleNamespace

from app.execution.executors.human_executor import HumanExecutor
from app.execution.executors.constants import EXECUTION_STATUS_WAITING
from app.execution.runtime.dag_scheduler import get_ready_steps
from app.workflow_execution.schemas.action_result import ActionResult


def _config(configuration: dict):
    """Minimal ActionConfiguration stand-in (executor reads .id/.configuration)."""
    return SimpleNamespace(id=1, configuration=configuration)


# ── HumanExecutor ─────────────────────────────────────────────────────────────

def test_execute_returns_action_result():
    result = HumanExecutor().execute(_config({"prompt": "Approve?"}), {})
    assert isinstance(result, ActionResult)


def test_execute_emits_waiting_marker():
    result = HumanExecutor().execute(_config({"prompt": "Approve?"}), {})
    assert result.metadata["execution_status"] == EXECUTION_STATUS_WAITING


def test_execute_carries_human_task_spec():
    result = HumanExecutor().execute(
        _config({"prompt": "Approve loan?", "timeout_seconds": 3600, "on_timeout": "approve"}),
        {},
    )
    spec = result.metadata["human_task"]
    assert spec["prompt"] == "Approve loan?"
    assert spec["timeout_seconds"] == 3600
    assert spec["on_timeout"] == "approve"


def test_on_timeout_defaults_to_reject():
    result = HumanExecutor().execute(_config({"prompt": "x"}), {})
    assert result.metadata["human_task"]["on_timeout"] == "reject"


def test_invalid_on_timeout_falls_back_to_reject():
    result = HumanExecutor().execute(
        _config({"prompt": "x", "on_timeout": "escalate"}), {}
    )
    assert result.metadata["human_task"]["on_timeout"] == "reject"


def test_default_prompt_when_missing():
    result = HumanExecutor().execute(_config({}), {})
    assert result.metadata["human_task"]["prompt"]


# ── get_ready_steps waiting behaviour ─────────────────────────────────────────

_STEPS = [
    {"id": "a", "depends_on": []},
    {"id": "b", "depends_on": ["a"]},
    {"id": "c", "depends_on": ["b"]},
]


def test_ready_steps_basic_dependency_order():
    ready = get_ready_steps(_STEPS, completed_steps=set(), failed_steps=set())
    assert [s["id"] for s in ready] == ["a"]


def test_completed_dependency_unlocks_next():
    ready = get_ready_steps(_STEPS, completed_steps={"a"}, failed_steps=set())
    assert [s["id"] for s in ready] == ["b"]


def test_waiting_step_is_not_rescheduled():
    # 'b' is waiting on a human decision; it must not be returned as ready
    # even though its dependency 'a' is complete.
    ready = get_ready_steps(
        _STEPS,
        completed_steps={"a"},
        failed_steps=set(),
        waiting_steps={"b"},
    )
    assert ready == []


def test_downstream_blocked_while_waiting():
    # 'b' waiting means 'c' can never be ready (its dep 'b' isn't complete).
    ready = get_ready_steps(
        _STEPS,
        completed_steps={"a"},
        failed_steps=set(),
        waiting_steps={"b"},
    )
    assert all(s["id"] != "c" for s in ready)
