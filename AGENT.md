# AGENT.md — MFlows Development Guide

## Purpose

MFlows is a workflow automation engine. It accepts workflow definitions in DSL or natural language, compiles them to an AST, and executes them as deterministic DAGs.

---

## Core Principle

All workflow creation methods must produce the same AST.

```
DSL               → ParseNode list → ASTBuilder → WorkflowAST
Natural Language  → ParseNode list → ASTBuilder → WorkflowAST
LLM output        → ParseNode list → ASTBuilder → WorkflowAST
                                                       ↓
                                              ASTValidator
                                                       ↓
                                           WorkflowComplier
                                                       ↓
                                         Workflow Definition
                                           (parsed_rule_json)
                                                       ↓
                                           Runtime Processor
                                                       ↓
                                             DAG Execution
```

The compiler and runtime never know or care how the AST was produced.

---

## Rules

- Never execute raw LLM output. Always pass through AST pipeline first.
- Always validate AST before compilation (`ASTValidator`).
- Always compile before runtime (`WorkflowComplier`).
- Keep NLP isolated from execution — `app/nlp/` must not import from `app/execution/`.
- Keep runtime deterministic — no ML or LLM calls inside execution layer.
- Do not place business logic inside `runtime_processor`.
- Do not place NLP logic inside the execution layer.

---

## Development Order

```
Parser → AST → Validator → Compiler → Runtime
```

Never bypass the pipeline. Every input source must enter at the top.

---

## Module Boundaries

| Layer | Location | Responsibility |
|---|---|---|
| NL Extraction | `app/nlp/nl/` | NL sentence → ParseNode list |
| DSL Parsing | `app/nlp/parsers/` `app/parsers/` | DSL text → ParseNode list |
| AST | `app/nlp/ast/` | ParseNode list → WorkflowAST, validation |
| Compiler | `app/nlp/complier/` | WorkflowAST → DAG dict (v2) |
| Runtime | `app/execution/runtime/` | DAG dict → step execution |
| Dispatcher | `app/execution/dispatcher.py` | action name → handler function |

---

## Protected — Do Not Modify

These components have stable, tested behavior. Only bug fixes allowed:

- `app/execution/runtime/runtime_processor.py`
- `app/execution/runtime/dag_executor.py`
- `app/workers/retry_worker.py`
- `app/workers/reaper_worker.py`
- `app/execution/dedupe.py`
- `app/execution/runtime/workflow_finalizer.py`
- `app/db/` and `alembic/` (existing migrations)
- All existing API contracts in `app/routes/`

---

## Key Data Types

### ParseNode (`app/nlp/models.py`)
```python
ParseNode(step_id="1", event="payment_due", action="send_reminder", depends_on=[])
```

### WorkflowAST (`app/nlp/ast/schema.py`)
```python
WorkflowAST(
    trigger=TriggerNode(event="payment_due"),
    steps=[
        StepNode(id="1", action="send_reminder", depends_on=[]),
        StepNode(id="2", action="notify_manager", depends_on=["1"]),
    ]
)
```

### Compiled DAG dict (runtime-compatible)
```python
{
    "version": "v2",
    "trigger": {"event_type": "payment_due"},
    "steps": [
        {"id": "1", "action": "send_reminder", "depends_on": [], "config": {}},
        {"id": "2", "action": "notify_manager", "depends_on": ["1"], "config": {}},
    ]
}
```

---

## Registries

Triggers and actions are defined in two places that must stay in sync:

| File | Purpose |
|---|---|
| `app/llm/schemas.py` | LLM prompt validation (ALLOWED_TRIGGERS, ALLOWED_ACTIONS) |
| `app/parsers/dag_validator.py` | DSL DAG validation |
| `app/nlp/registry/trigger_registry.py` | NLP trigger registry |
| `app/nlp/registry/action_registry.py` | NLP action registry |
| `app/nlp/nl/patterns.py` | NL phrase → canonical identifier mapping |

When adding a new trigger or action, update all five.

---

## Adding a New Input Source

1. Produce `List[ParseNode]` from your source
2. Pass to `WorkflowASTBuilder().build(nodes)`
3. Validate with `ASTValidator().validate(ast)`
4. Compile with `WorkflowComplier().compile(ast)`
5. Store result as `parsed_rule_json`

Do not write a custom compiler or bypass any step.

---

## NLP Phase 2.4 — Completed

Files delivered:

| File | Role |
|---|---|
| `app/nlp/nl/patterns.py` | Phrase → canonical identifier dictionaries |
| `app/nlp/nl/intent_extractor.py` | Rule-based NL → trigger + action list |
| `app/nlp/nl/nl_service.py` | NL sentence → WorkflowAST entry point |
| `tests/nlp/test_nl_pipeline.py` | 12 test cases |

---

## Next Milestone — Prompt Service

```
Prompt Templates
      ↓
Intent Extraction  (structured LLM call → trigger + actions)
      ↓
    AST
      ↓
  Compiler
      ↓
  Runtime
```

The Prompt Service sits between LLM output and the AST pipeline. It must:
- Define prompt templates per workflow domain
- Parse LLM structured output into `List[ParseNode]`
- Never pass raw LLM text to the compiler or runtime
- Feed into the existing `ASTBuilder → ASTValidator → WorkflowComplier` chain
