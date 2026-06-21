"""
test_full_pipeline.py

End-to-end pipeline tests: DSL generator → compile → save → execute → COMPLETED

No LLM needed — workflow JSON is injected directly.
Tests cover: sequential, parallel, diamond, deep chain, multi-branch patterns.

Requirements:
  docker-compose up  (all services including worker)

Run:
  .venv\\Scripts\\python.exe test_full_pipeline.py
  .venv\\Scripts\\python.exe test_full_pipeline.py --id P01
"""

import sys
import time
import argparse
import requests
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()

from app.db.session import SessionLocal
from app.models.workflow_execution import WorkflowExecution
from app.dsl.dsl_generator import DSLGenerator
from app.nlp.parsers.rule_parser import RuleParser
from app.nlp.ast.builder import WorkflowASTBuilder
from app.nlp.ast.validator import ASTValidator
from app.nlp.complier.workflow_complier import WorkflowComplier
from app.workflow.workflow_compiler_service import WorkflowCompilerService
from app.workflow.workflow_persistence_service import WorkflowPersistenceService

BASE_URL = "http://localhost:8000"
POLL_TIMEOUT = 60
POLL_INTERVAL = 2


@dataclass
class PipelineCase:
    id: str
    name: str
    description: str
    workflow_type: str
    domain: str
    user_request: str
    workflow_json: dict


CASES = [

    # ── P01: Parallel (fan-out) ───────────────────────────────────────────────
    # escalate + notify run in parallel, no join
    PipelineCase(
        id="P01",
        name="p01-parallel-fanout",
        description="Payment missed → escalate + notify (parallel, no join)",
        workflow_type="finance",
        domain="finance",
        user_request="When payment is missed escalate case and notify manager",
        workflow_json={
            "workflow": {
                "triggers": [{"name": "payment_missed"}],
                "actions": [
                    {"name": "escalate_case",  "dependencies": []},
                    {"name": "notify_manager", "dependencies": []},
                ]
            }
        }
    ),

    # ── P02: Sequential chain ─────────────────────────────────────────────────
    # remind → escalate → notify (strict order)
    PipelineCase(
        id="P02",
        name="p02-sequential-chain",
        description="Payment due → remind → escalate → notify (sequential)",
        workflow_type="finance",
        domain="finance",
        user_request="When payment is due send reminder then escalate case then notify manager",
        workflow_json={
            "workflow": {
                "triggers": [{"name": "payment_due"}],
                "actions": [
                    {"name": "send_reminder",  "dependencies": []},
                    {"name": "escalate_case",  "dependencies": ["send_reminder"]},
                    {"name": "notify_manager", "dependencies": ["escalate_case"]},
                ]
            }
        }
    ),

    # ── P03: Diamond ─────────────────────────────────────────────────────────
    # assign → (notify_customer + notify_manager) → close_case
    PipelineCase(
        id="P03",
        name="p03-diamond",
        description="Ticket created → assign → notify×2 → close (diamond)",
        workflow_type="support",
        domain="support",
        user_request="When ticket created assign support agent then notify customer and notify manager then close case",
        workflow_json={
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
    ),

    # ── P04: Diamond with audit tail ─────────────────────────────────────────
    # escalate + notify → audit (two inputs merge then one more step)
    PipelineCase(
        id="P04",
        name="p04-diamond-audit",
        description="Payment missed → escalate + notify → audit (diamond + tail)",
        workflow_type="finance",
        domain="finance",
        user_request="When payment is missed escalate case and notify manager then create audit record",
        workflow_json={
            "workflow": {
                "triggers": [{"name": "payment_missed"}],
                "actions": [
                    {"name": "escalate_case",       "dependencies": []},
                    {"name": "notify_manager",      "dependencies": []},
                    {"name": "create_audit_record", "dependencies": ["escalate_case", "notify_manager"]},
                ]
            }
        }
    ),

    # ── P05: Deep sequential chain (4 steps) ─────────────────────────────────
    PipelineCase(
        id="P05",
        name="p05-deep-chain",
        description="Fraud detected → lock → flag → notify → audit (4-step chain)",
        workflow_type="finance",
        domain="finance",
        user_request="When fraud detected lock account then flag for review then notify manager then create audit record",
        workflow_json={
            "workflow": {
                "triggers": [{"name": "fraud_detected"}],
                "actions": [
                    {"name": "lock_account",        "dependencies": []},
                    {"name": "flag_for_review",     "dependencies": ["lock_account"]},
                    {"name": "notify_manager",      "dependencies": ["flag_for_review"]},
                    {"name": "create_audit_record", "dependencies": ["notify_manager"]},
                ]
            }
        }
    ),

    # ── P06: Wide parallel (3 parallel branches) ─────────────────────────────
    PipelineCase(
        id="P06",
        name="p06-wide-parallel",
        description="Critical vitals → alert + notify + escalate (3-way parallel)",
        workflow_type="health",
        domain="health",
        user_request="When critical vitals detected alert care team and notify manager and escalate to specialist",
        workflow_json={
            "workflow": {
                "triggers": [{"name": "critical_vitals"}],
                "actions": [
                    {"name": "alert_care_team",       "dependencies": []},
                    {"name": "notify_manager",        "dependencies": []},
                    {"name": "escalate_to_specialist","dependencies": []},
                ]
            }
        }
    ),

    # ── P07: Single action (minimal) ─────────────────────────────────────────
    PipelineCase(
        id="P07",
        name="p07-single-action",
        description="Payment due → send reminder (single step, minimal)",
        workflow_type="finance",
        domain="finance",
        user_request="When payment is due send reminder",
        workflow_json={
            "workflow": {
                "triggers": [{"name": "payment_due"}],
                "actions": [
                    {"name": "send_reminder", "dependencies": []},
                ]
            }
        }
    ),

    # ── P08: Support full flow ────────────────────────────────────────────────
    # assign → send_update → resolve (sequential support flow)
    PipelineCase(
        id="P08",
        name="p08-support-flow",
        description="Ticket created → assign → update customer → resolve (support flow)",
        workflow_type="support",
        domain="support",
        user_request="When ticket created assign support agent then send customer update then resolve ticket",
        workflow_json={
            "workflow": {
                "triggers": [{"name": "ticket_created"}],
                "actions": [
                    {"name": "assign_support_agent", "dependencies": []},
                    {"name": "send_customer_update", "dependencies": ["assign_support_agent"]},
                    {"name": "resolve_ticket",       "dependencies": ["send_customer_update"]},
                ]
            }
        }
    ),

]


def build_compiler() -> WorkflowCompilerService:
    return WorkflowCompilerService(
        dsl_generator=DSLGenerator(),
        rule_parser=RuleParser(),
        ast_builder=WorkflowASTBuilder(),
        ast_validator=ASTValidator(),
        workflow_compiler=WorkflowComplier(),
    )


def run_case(case: PipelineCase) -> bool:
    print(f"\n{'─' * 65}")
    print(f"  [{case.id}] {case.description}")
    print(f"{'─' * 65}")

    db = SessionLocal()
    try:
        # Compile
        compiler = build_compiler()
        compile_result = compiler.compile(case.workflow_type, case.workflow_json)
        dsl = compile_result["dsl"]
        compiled = compile_result["compiled"]

        print(f"\n  DSL:")
        for line in dsl.splitlines():
            print(f"    {line}")
        print(f"  Steps: {len(compiled['steps'])}  trigger: {compiled['trigger']['event_type']}")

        # Save
        persistence = WorkflowPersistenceService()
        saved = persistence.save(
            db=db,
            name=case.name,
            domain=case.domain,
            user_request=case.user_request,
            compile_result=compile_result,
        )
        workflow_id = saved["workflow_id"]
        print(f"\n  Saved  workflow_id={workflow_id}")

        # Execute
        resp = requests.post(
            f"{BASE_URL}/api/execute/",
            json={"workflow_id": workflow_id, "entity_id": f"test-{case.id.lower()}"},
            timeout=10,
        )
        if resp.status_code != 200 or not resp.json().get("success"):
            print(f"\n  ❌ Execute failed  {resp.status_code}: {resp.text[:200]}")
            return False

        workflow_execution_id = resp.json()["workflow_execution_id"]
        print(f"  Queued workflow_execution_id={workflow_execution_id}")

        # Poll
        print(f"  Polling", end="", flush=True)
        deadline = time.time() + POLL_TIMEOUT
        final_status = None

        while time.time() < deadline:
            db.expire_all()
            execution = db.query(WorkflowExecution).filter(
                WorkflowExecution.id == workflow_execution_id
            ).first()
            if execution:
                final_status = execution.status
                print(f"  {final_status}", end="", flush=True)
                if final_status in ("COMPLETED", "FAILED", "DLQ"):
                    break
            time.sleep(POLL_INTERVAL)

        print()
        if final_status == "COMPLETED":
            print(f"\n  ✅ PASSED")
            return True
        else:
            print(f"\n  ❌ FAILED — final status: {final_status}")
            return False

    except Exception as e:
        import traceback
        print(f"\n  ❌ EXCEPTION — {type(e).__name__}: {e}")
        print(traceback.format_exc())
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Full pipeline test suite")
    parser.add_argument("--id", help="Run a single case by ID (e.g. P01)")
    args = parser.parse_args()

    cases = CASES
    if args.id:
        cases = [c for c in CASES if c.id == args.id.upper()]
        if not cases:
            print(f"No case with id '{args.id}'")
            sys.exit(1)

    print("\n" + "=" * 65)
    print(f"FULL PIPELINE TEST — {len(cases)} cases")
    print("=" * 65)

    results = [run_case(c) for c in cases]
    passed = sum(results)
    failed = len(results) - passed

    print("\n" + "=" * 65)
    print(f"TOTAL: {len(results)}   ✅ PASSED: {passed}   ❌ FAILED: {failed}")
    print("=" * 65)

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

