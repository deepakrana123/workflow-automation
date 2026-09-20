"""
app/agent/agent_runner.py

AgentRunner — runs a workflow "as an agent" (OPT-IN, human-in-the-loop).

Design guarantees (per product owner):
  * OPT-IN ONLY. This is never auto-attached to a workflow and is not a workflow
    execution_type. Existing workflows and their normal DAG execution are untouched.
    A workflow becomes an agent only when this runner is explicitly invoked.
  * ALWAYS ASK FIRST. Before EVERY action the runner calls the injected `approver`
    callback with the proposed action + reasoning. Nothing executes unless the
    approver returns True. The default approver denies (safe by default).
  * FULL OBSERVABILITY. Every planner decision, approval outcome, action dispatch,
    result and validation is emitted as a structured `agent_*` log event and also
    returned in the run record (trajectory).

The agent's TOOLSET is exactly the workflow's action set (bounded scope). Each
tool's input_schema/output_schema is its function signature. Tools are resolved
via the same `resolve_action_definition` the engine uses, and executed via the
same `get_executor` executors — so the agent reuses production behavior.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.workflow import Workflow
from app.execution.runtime.config_resolver import resolve_action_definition
from app.execution.executors.registry import get_executor
from app.execution.runtime.output_validation import validate_outputs
from app.workflow_execution.schemas.workflow_context import WorkflowContext
from app.nlp.llm_manager.llm_manager import LLMManager

# Fallback write-detection when an ActionDefinition has no is_state_changing flag.
_WRITE_RE = re.compile(
    r"^(create|update|disburse|approve|reject|sanction|assign|escalat|register|send|"
    r"initiate|collect|upload|schedule|generate|block|close|waive|link|onboard|mark|"
    r"route|charge|release)",
    re.IGNORECASE,
)

# An approver is asked before every action. It receives the proposed-action dict and
# returns True to allow execution, False to hold. Default = deny (safe).
Approver = Callable[[dict], bool]


def _deny(_proposal: dict) -> bool:
    return False


@dataclass
class AgentTurn:
    turn: int
    reasoning: str = ""
    action: str | None = None
    args: dict = field(default_factory=dict)
    is_state_changing: bool = False
    approved: bool | None = None
    executed: bool = False
    input_missing: list = field(default_factory=list)
    outputs: dict = field(default_factory=dict)
    output_missing: list = field(default_factory=list)
    error: str | None = None
    note: str | None = None


class AgentRunner:
    def __init__(
        self,
        db: Session,
        *,
        resolve_fn=resolve_action_definition,
        llm: LLMManager | None = None,
        executor_getter=get_executor,
        max_steps: int = 20,
    ):
        self.db = db
        self._resolve = resolve_fn
        self._llm = llm or LLMManager()
        self._get_executor = executor_getter
        self.max_steps = max_steps

    # ── public API ─────────────────────────────────────────────────────────────

    def run(
        self,
        workflow_id: int,
        inputs: dict[str, Any] | None = None,
        *,
        approver: Approver = _deny,
        workspace_id: int | None = None,
        trace_id: str | None = None,
    ) -> dict:
        """Run the workflow as an agent. Returns a run record (never raises)."""
        started = time.time()
        wf = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if wf is None:
            return {"status": "ERROR", "error": "workflow_not_found", "workflow_id": workflow_id}
        ws_id = workspace_id if workspace_id is not None else getattr(wf, "workspace_id", None)

        toolset = self._toolset(wf)
        goal = self._goal(wf)
        specs = self._tool_specs(toolset, ws_id)

        logger.info("agent_run_started", extra={"extra_data": {
            "workflow_id": workflow_id, "workspace_id": ws_id,
            "toolset": toolset, "goal": goal, "trace_id": trace_id,
        }})

        ctx = WorkflowContext()
        ctx.outputs.update(inputs or {})
        called: list[str] = []
        trajectory: list[dict] = []
        last_error: str | None = None
        status = "COMPLETED"

        for turn_no in range(1, self.max_steps + 1):
            plan = self._plan(goal, specs, dict(ctx.outputs), called, last_error)
            last_error = None
            turn = AgentTurn(turn=turn_no, reasoning=str(plan.get("reasoning", ""))[:300])

            if plan.get("done"):
                turn.note = "planner_signalled_done"
                logger.info("agent_done", extra={"extra_data": {
                    "workflow_id": workflow_id, "turn": turn_no, "reasoning": turn.reasoning}})
                trajectory.append(turn.__dict__)
                break

            action = plan.get("action")
            turn.action = action
            turn.args = plan.get("args") or {}

            spec = next((s for s in specs if s["name"] == action), None)
            if spec is None:
                turn.error = f"unknown_tool:{action}"
                last_error = turn.error
                logger.warning("agent_invalid_tool", extra={"extra_data": {
                    "workflow_id": workflow_id, "turn": turn_no, "action": action}})
                trajectory.append(turn.__dict__)
                continue

            turn.is_state_changing = spec["is_state_changing"]

            # ── ALWAYS ASK FIRST ────────────────────────────────────────────────
            proposal = {
                "workflow_id": workflow_id, "turn": turn_no, "action": action,
                "args": turn.args, "is_state_changing": turn.is_state_changing,
                "reasoning": turn.reasoning,
            }
            logger.info("agent_action_proposed", extra={"extra_data": proposal})
            allowed = bool(approver(proposal))
            turn.approved = allowed
            logger.info("agent_approval_decision", extra={"extra_data": {
                "workflow_id": workflow_id, "turn": turn_no, "action": action, "approved": allowed}})
            if not allowed:
                turn.note = "held_pending_approval"
                trajectory.append(turn.__dict__)
                status = "AWAITING_APPROVAL"
                break

            # ── execute the approved tool via the real executor ─────────────────
            ad = self._resolve(self.db, action, ws_id)
            if ad is None:
                turn.error = "unresolved_action"
                last_error = turn.error
                trajectory.append(turn.__dict__)
                continue

            call_ctx = dict(ctx.outputs)
            call_ctx.update(turn.args)
            turn.input_missing = validate_outputs(call_ctx, getattr(ad, "input_schema", None))["missing"]

            etype = (getattr(ad, "execution_template", None) or {}).get("execution_type", "python")
            try:
                result = self._get_executor(etype).execute(action_definition=ad, context=call_ctx)
                turn.executed = True
                turn.outputs = result.outputs or {}
                if not result.success:
                    turn.error = result.error or "action_failed"
            except Exception as exc:  # noqa: BLE001
                turn.error = f"{type(exc).__name__}: {exc}"

            turn.output_missing = validate_outputs(turn.outputs, getattr(ad, "output_schema", None))["missing"]

            logger.info("agent_action_executed", extra={"extra_data": {
                "workflow_id": workflow_id, "turn": turn_no, "action": action,
                "exec_type": etype, "success": turn.error is None,
                "output_keys": list(turn.outputs.keys()), "error": turn.error,
            }})

            if turn.error is None:
                ctx.update_step(action, turn.outputs)
                called.append(action)
            trajectory.append(turn.__dict__)
        else:
            status = "MAX_STEPS_REACHED"

        record = {
            "workflow_id": workflow_id, "workspace_id": ws_id, "goal": goal,
            "toolset": toolset, "status": status, "called": called,
            "turns": len(trajectory), "trajectory": trajectory,
            "final_context": ctx.outputs, "elapsed_ms": int((time.time() - started) * 1000),
        }
        logger.info("agent_run_finished", extra={"extra_data": {
            "workflow_id": workflow_id, "status": status, "called": called,
            "turns": len(trajectory)}})
        return record

    def plan_only(self, workflow_id: int, inputs: dict | None = None,
                  workspace_id: int | None = None) -> dict:
        """Propose the FIRST action without executing anything (pure 'ask first')."""
        wf = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if wf is None:
            return {"status": "ERROR", "error": "workflow_not_found"}
        ws_id = workspace_id if workspace_id is not None else getattr(wf, "workspace_id", None)
        specs = self._tool_specs(self._toolset(wf), ws_id)
        plan = self._plan(self._goal(wf), specs, dict(inputs or {}), [], None)
        return {"workflow_id": workflow_id, "proposed": plan, "toolset": [s["name"] for s in specs]}

    # ── internals ───────────────────────────────────────────────────────────────

    def _toolset(self, wf: Workflow) -> list[str]:
        steps = (wf.parsed_rule_json or {}).get("steps", [])
        names: list[str] = []
        for s in steps:
            a = s.get("action")
            if a and a not in names:
                names.append(a)
        return names

    def _goal(self, wf: Workflow) -> str:
        trigger = (wf.parsed_rule_json or {}).get("trigger", {}).get("event_type", "workflow_triggered")
        return (f"Achieve the objective of workflow '{wf.name}' (trigger: {trigger}) by using the "
                f"available tools. Call each required tool as needed; set done=true when the "
                f"objective is met.")

    def _tool_specs(self, names: list[str], workspace_id: int | None) -> list[dict]:
        specs = []
        for n in names:
            ad = self._resolve(self.db, n, workspace_id)
            if ad is None:
                continue
            ischema = getattr(ad, "input_schema", None) or {}
            props = ischema.get("properties", {}) if isinstance(ischema, dict) else {}
            is_write = getattr(ad, "is_state_changing", None)
            if is_write is None:
                is_write = bool(_WRITE_RE.match(n))
            specs.append({
                "name": n,
                "description": (getattr(ad, "display_name", None) or n),
                "inputs": {k: (props[k] or {}).get("type") for k in props},
                "required": ischema.get("required", []) if isinstance(ischema, dict) else [],
                "is_state_changing": bool(is_write),
            })
        return specs

    def _plan(self, goal: str, specs: list[dict], context: dict,
              called: list[str], last_error: str | None) -> dict:
        prompt = (
            "You are a loan workflow AGENT. Achieve the GOAL by choosing ONE tool per turn, "
            "using ONLY the listed TOOLS and argument values available in CONTEXT. Do not repeat "
            "a tool in CALLED unless necessary. When the goal is met, set done=true.\n"
            "Respond with ONE JSON object ONLY (no prose, no markdown): "
            '{"reasoning": str (<=20 words), "done": bool, "action": str|null, "args": object}.\n\n'
            f"GOAL: {goal}\n"
            f"TOOLS: {json.dumps(specs, ensure_ascii=False)}\n"
            f"CONTEXT: {json.dumps(context, ensure_ascii=False)}\n"
            f"CALLED: {json.dumps(called)}\n"
            f"LAST_ERROR: {last_error}\n"
        )
        try:
            result = self._llm.generate(prompt)
            text = result.get("output", "") if isinstance(result, dict) else str(result)
        except Exception as exc:  # noqa: BLE001
            logger.warning("agent_planner_llm_failed", extra={"extra_data": {"error": str(exc)}})
            return {"done": True, "reasoning": "planner_error", "action": None, "args": {}}
        m = re.search(r"\{.*\}", text or "", re.S)
        if not m:
            return {"done": True, "reasoning": "planner_unparseable", "action": None, "args": {}}
        try:
            return json.loads(m.group(0))
        except Exception:  # noqa: BLE001
            return {"done": True, "reasoning": "planner_bad_json", "action": None, "args": {}}
