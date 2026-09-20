# Build Guide — Promote the Agent Prototype to a Production `agent` Executor

> Status: build plan. The eval-layer prototype (`scripts/e2e/agent_prototype.py`) already
> validated the full loop (10/10 tools, guardrails, context threading) on the curated catalog.
> This describes how to make it a first-class, governed executor. **Additive — no existing
> execution logic is rewritten.**

## 0. Verdict: yes, and it's additive
The engine dispatches each step by `execution_template.execution_type` via `ExecutorRegistry`
(`python` / `http` / `human_task`). Adding an **`agent`** type is a new registry entry + one new
executor class. A workflow step with `execution_type=agent` then runs the planner loop. Everything
else (DAG scheduler, `WorkflowContext`, rules engine, RBAC, retries, trace) is reused unchanged.

## 1. What we already proved (prototype → production mapping)
| Agent need | Prototype used | Production equivalent |
|---|---|---|
| Tools | curated `catalog_curated.json` | `resolve_action_definition` (catalog / workspace snapshot) |
| Tool signatures | `input_schema` / `output_schema` | same (already on `ActionDefinition`) |
| Run a tool | `get_executor(python\|http).execute` | same |
| Memory | `WorkflowContext` | same |
| Write-action gate | mock approval on `is_state_changing` | `HumanExecutor` + RBAC `allowed_roles` |
| Input/output check | `validate_outputs` | `validate_outputs` (+ new input validation) |
| Planning | OpenRouter JSON planner | `LLMManager` (JSON-only or function-calling) |

## 2. New pieces to add (all additive)
1. `ExecutionType.AGENT = "agent"` constant (executors/constants).
2. `app/execution/executors/agent_executor.py` — `AgentExecutor(BaseExecutor)`:
   - `execute(action_definition, context) -> ActionResult`
   - reads its **step config** (see §3), runs the plan→act→observe loop, returns a final
     `ActionResult` (success + a summary of the sub-actions taken + merged outputs).
3. Register it: `ExecutorRegistry({..., ExecutionType.AGENT: AgentExecutor()})`.
No change to `step_executor` dispatch — it already calls `get_executor(execution_type)`.

## 3. Agent step config (stored on the step, user-editable)
```json
{
  "execution_type": "agent",
  "configuration": {
    "goal": "Complete KYC + verification + eligibility so the lead is decision-ready.",
    "toolset": "workspace",              // or explicit ["verify_pan","run_bureau_check",...]
    "max_steps": 15,
    "require_approval_for_writes": true,
    "planner_model": "…"                 // optional override
  }
}
```
`toolset="workspace"` bounds the agent to the workspace's mapped actions (safest); an explicit list
scopes it to one workflow's action set (what the prototype did).

## 4. The loop (per turn) — from the validated prototype
1. Build the tool list from the toolset (name, description, `input_schema`, `is_state_changing`).
2. LLM planner (via `LLMManager`) returns `{reasoning, done, action, args}` (JSON-only).
3. Validate `args` against the tool's `input_schema`.
4. **Guardrails:** if `is_state_changing` → route through `HumanExecutor` (real approval) and check
   RBAC `allowed_roles`; run the rules engine (`evaluate_step_rules`) as today.
5. Execute the tool: `get_executor(tool.execution_type).execute(action_def, context)`.
6. Validate outputs against `output_schema`; merge into `WorkflowContext`; record an `ExecutionStep`
   + `trace_service` events (so every tool call is audited).
7. Repeat until `done` / goal met / `max_steps`.

## 5. Guardrails (banking-safe by construction)
- Toolset bounded to the workspace's actions.
- Writes gated by `HumanExecutor` + RBAC.
- Every arg validated against `input_schema`; every result against `output_schema`.
- Full trace via `ExecutionStep` + `trace_service`; step budget prevents runaway loops.
- **Deterministic fallback:** if the planner errors/loops, fall back to the DAG order.

## 6. Hybrid workflows
Because it's just another `execution_type`, a workflow can mix deterministic steps and an agent
step (e.g. deterministic KYC gate → `agent` step for adaptive verification → deterministic decision).

## 7. Phases
1. **AgentExecutor MVP** — single agent step, explicit toolset, JSON planner, approval gate. (Prototype is the reference.)
2. **Guardrail integration** — wire `HumanExecutor` + RBAC + rules engine instead of the mock gate.
3. **Hybrid** — deterministic + agent steps in one DAG.
4. **Reflection/retry** — let the planner react to step errors; add loop/repeat detection.

## 8. Testing
Reuse `scripts/e2e/agent_prototype.py` as the behavioral test harness (curated catalog, real
executors). Add unit tests for arg-validation, the write-approval gate, and step-budget termination.

## 9. Files touched (summary)
- **New:** `app/execution/executors/agent_executor.py`.
- **Additive edits:** register `AGENT` in `executors/registry.py` + constant; (optional) agent-step
  config validation. No rewrite of `runtime_processor`, `dag_executor`, `step_executor`, or existing executors.
