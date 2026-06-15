"""
test_dsl_pipeline.py

Tests the chain:
  LLM JSON output → DSLGenerator → RuleParser → ASTBuilder → ASTValidator → Compiler

No DB, no Docker, no API needed.
Run: .venv\Scripts\python.exe test_dsl_pipeline.py
"""

import json
from app.dsl.dsl_generator import DSLGenerator
from app.nlp.parsers.rule_parser import RuleParser
from app.nlp.ast.builder import WorkflowASTBuilder
from app.nlp.ast.validator import ASTValidator
from app.nlp.complier.workflow_complier import WorkflowComplier

# ── Simulated LLM JSON outputs (mirrors your 5 test cases) ───────────────────

CASES = [
    {
        "name": "A01 — payment missed → escalate + notify + audit",
        "workflow_type": "payments",
        "llm_output": {
            "workflow": {
                "triggers": [{"name": "payment_missed"}],
                "actions": [
                    {"name": "escalate_case",      "dependencies": []},
                    {"name": "notify_manager",     "dependencies": []},
                    {"name": "create_audit_record","dependencies": ["escalate_case", "notify_manager"]},
                ]
            }
        }
    },
    {
        "name": "A02 — payment missed → escalate + notify",
        "workflow_type": "payments",
        "llm_output": {
            "workflow": {
                "triggers": [{"name": "payment_missed"}],
                "actions": [
                    {"name": "escalate_case",  "dependencies": []},
                    {"name": "notify_manager", "dependencies": []},
                ]
            }
        }
    },
    {
        "name": "A03 — payment due → remind → escalate → notify",
        "workflow_type": "payments",
        "llm_output": {
            "workflow": {
                "triggers": [{"name": "payment_due"}],
                "actions": [
                    {"name": "send_reminder",  "dependencies": []},
                    {"name": "escalate_case",  "dependencies": ["send_reminder"]},
                    {"name": "notify_manager", "dependencies": ["escalate_case"]},
                ]
            }
        }
    },
    {
        "name": "A04 — fraud detected → lock → flag → notify",
        "workflow_type": "payments",
        "llm_output": {
            "workflow": {
                "triggers": [{"name": "fraud_detected"}],
                "actions": [
                    {"name": "lock_account",   "dependencies": []},
                    {"name": "flag_for_review","dependencies": ["lock_account"]},
                    {"name": "notify_manager", "dependencies": ["flag_for_review"]},
                ]
            }
        }
    },
    {
        "name": "A05 — ticket created → assign → notify×2 → close",
        "workflow_type": "support",
        "llm_output": {
            "workflow": {
                "triggers": [{"name": "ticket_created"}],
                "actions": [
                    {"name": "assign_support_agent",  "dependencies": []},
                    {"name": "send_customer_update",  "dependencies": ["assign_support_agent"]},
                    {"name": "notify_manager",        "dependencies": ["assign_support_agent"]},
                    {"name": "close_case",            "dependencies": ["send_customer_update", "notify_manager"]},
                ]
            }
        }
    },
]

# ── Pipeline ──────────────────────────────────────────────────────────────────

dsl_gen   = DSLGenerator()
parser    = RuleParser()
builder   = WorkflowASTBuilder()
validator = ASTValidator()
compiler  = WorkflowComplier()

print("=" * 70)
print("DSL PIPELINE TEST")
print("=" * 70)

passed = 0
failed = 0

for case in CASES:
    print(f"\n── {case['name']} ──")
    try:
        # Step 1: JSON → DSL string
        dsl = dsl_gen.generate(case["workflow_type"], case["llm_output"])
        print(f"\n  DSL:\n{chr(10).join('    ' + l for l in dsl.splitlines())}")

        # Step 2: DSL → ParseNodes
        nodes = parser.parse(dsl)
        print(f"\n  ParseNodes ({len(nodes)}):")
        for n in nodes:
            print(f"    step={n.step_id}  event={n.event}  action={n.action}  depends_on={n.depends_on}")

        # Step 3: ParseNodes → AST
        ast = builder.build(nodes)

        # Step 4: Validate AST
        validator.validate(ast)

        # Step 5: AST → compiled dict
        compiled = compiler.compile(ast)
        print(f"\n  Compiled:")
        print(f"    trigger: {compiled['trigger']}")
        for step in compiled["steps"]:
            print(f"    step {step['id']}: {step['action']}  depends_on={step['depends_on']}")

        print(f"\n  ✅ PASSED")
        passed += 1

    except Exception as e:
        print(f"\n  ❌ FAILED — {type(e).__name__}: {e}")
        failed += 1

print("\n" + "=" * 70)
print(f"TOTAL: {len(CASES)}   ✅ PASSED: {passed}   ❌ FAILED: {failed}")
print("=" * 70)
