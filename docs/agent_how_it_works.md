# How the Agent Works (opt-in, always-ask, observable)

> Implemented additively in `app/agent/agent_runner.py`. It is **not** wired into normal
> workflow execution and is **not** a workflow `execution_type`. Existing workflows and their
> DAG execution are untouched. A workflow runs "as an agent" **only** when `AgentRunner` is
> explicitly invoked (the "Run as Agent" button/endpoint).

## 1. Opt-in, never automatic
- Normal workflows keep running through `runtime_processor`/DAG exactly as before.
- Turning a workflow into an agent does **not** modify or convert the stored workflow. The
  runner just *reads* the workflow's action set and runs a planning loop over it. The workflow
  definition is never changed. (Frontend: a "Run as Agent" button that calls the endpoint.)

## 2. The toolset = the workflow's own actions
`AgentRunner` takes the workflow's steps as its **bounded toolset** — the agent can only call
actions that already belong to that workflow. Each tool's `input_schema`/`output_schema`
(from the catalog, resolved via the same `resolve_action_definition` the engine uses) is its
function signature; `is_state_changing` marks write actions.

## 3. Always ask first (human-in-the-loop)
Before **every** action the runner calls an `approver` callback with the proposed action +
args + reasoning + whether it's state-changing. **Nothing executes unless the approver returns
True.** The default approver **denies** (safe by default). In the demo run, all 10 actions were
proposed for approval (3 of them write-actions explicitly flagged) before execution.

Two usage modes:
- `plan_only(...)` — returns the proposed next action **without executing anything** (pure "ask").
- `run(..., approver=...)` — loops plan → **ask** → (if approved) act → observe, per turn. If the
  approver holds, the run stops with `status=AWAITING_APPROVAL`.

## 4. Plan → approve → act → observe (per turn)
1. **Plan** — the LLM (`LLMManager`, or an injected planner) is given the goal, the tools (with
   schemas), the current `WorkflowContext`, and the tools already called; it returns
   `{reasoning, done, action, args}` (JSON only).
2. **Ask** — `approver(proposal)`; on deny → stop (`AWAITING_APPROVAL`).
3. **Validate input** — args checked against the tool's `input_schema`.
4. **Act** — executed via the real `get_executor(python|http).execute(action_def, context)`.
5. **Validate output** — result checked against `output_schema`.
6. **Observe** — outputs merged into `WorkflowContext` for the next turn.
Loop until the planner sets `done`, the goal is met, or `max_steps` is hit.

## 5. Guardrails (banking-safe by construction)
- Toolset bounded to the workflow's actions (no arbitrary catalog access).
- **Every** action gated by the approver; write (`is_state_changing`) actions are flagged. In
  production the approver is backed by `HumanExecutor` + RBAC `allowed_roles`.
- Input/output validated against schemas each turn.
- `max_steps` budget prevents runaway loops.
- Deterministic fallback: if the planner errors/loops, fall back to normal DAG order.

## 6. Observability (everything is traced)
Each turn emits structured `agent_*` log events and is recorded in the returned trajectory:
`agent_run_started`, `agent_action_proposed`, `agent_approval_decision`,
`agent_action_executed` (with exec_type, success, output keys, error), `agent_done`,
`agent_run_finished`. The run record contains: goal, toolset, per-turn
`{action, args, is_state_changing, approved, executed, input_missing, outputs, output_missing,
error, reasoning}`, the final context, status, and elapsed time. (In production these also
attach to `ExecutionStep` + `trace_service` so an agent run is auditable like any execution.)

## 7. Status values
`COMPLETED` (goal met), `AWAITING_APPROVAL` (approver held an action),
`MAX_STEPS_REACHED`, `ERROR` (workflow not found).

## 8. What's built vs. next
- **Built (additive, tested):** `AgentRunner` — plan/ask/act/observe loop, approval gate,
  schema validation, context threading, observability. Verified on workflow 10:
  `COMPLETED`, 10/10 tools executed, 10 approvals (3 writes), full trajectory in
  `scripts/e2e_artifacts/71_agent_runner.json`. LLM planning proven separately by the
  prototype (`scripts/e2e/agent_prototype.py`, 10/10) when the model isn't rate-limited.
- **Next (needs your go — network-exposed):** the "Run as Agent" endpoint (`POST
  /api/workflows/{id}/agent/plan` + `/agent/run`) and mounting it, with the approver wired to
  `HumanExecutor`/RBAC. Held deliberately because exposing an action-triggering endpoint is the
  sensitive step.
