"""
test1.py

Full end-to-end test: NLP → LLM → compile → save → execute → COMPLETED
Uses real DB catalog, real LLM, real execution worker.

Run:
    docker-compose up   (all services)
    .venv\\Scripts\\python.exe test1.py
    .venv\\Scripts\\python.exe test1.py --id F01
    .venv\\Scripts\\python.exe test1.py --domain finance
"""

import sys
import time
import argparse
import requests
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from app.db.session import SessionLocal
from app.nlp.catalog.matcher import CatalogMatcher
from app.nlp.catalog.triggerRepository import TriggerDefinitionRepository
from app.nlp.catalog.actionRepository import ActionDefinitionRepository
from app.nlp.suitability.suitability_agent import SuitabilityAgent
from app.nlp.prompts.builder import PromptBuilder
from app.nlp.prompts.prompt_context import PromptContext
from app.nlp.llm_manager.llm_manager import LLMManager
from app.workflow.workflow_response_parser import WorkflowResponseParser
from app.workflow.workflow_schema_validator import WorkflowSchemaValidator
from app.workflow.workflow_validator import WorkflowValidator
from app.workflow.workflow_compiler_service import WorkflowCompilerService
from app.workflow.workflow_persistence_service import WorkflowPersistenceService
from app.models.workflow_execution import WorkflowExecution
from app.dsl.dsl_generator import DSLGenerator
from app.nlp.parsers.rule_parser import RuleParser
from app.nlp.ast.builder import WorkflowASTBuilder
from app.nlp.ast.validator import ASTValidator
from app.nlp.complier.workflow_complier import WorkflowComplier

BASE_URL = "http://localhost:8000"
POLL_TIMEOUT = 90
POLL_INTERVAL = 2


@dataclass
class E2ECase:
    id: str
    domain: str
    description: str
    user_request: str
    expect_success: bool = True


# ── Finance (12 cases) ────────────────────────────────────────────────────────
FINANCE_CASES = [
#     E2ECase("F01", "finance", "Payment missed → escalate + notify + audit",
#         "When payment is missed escalate case and notify manager then create audit record"),

#     E2ECase("F02", "finance", "Payment due → remind → escalate → notify",
#         "When payment is due send reminder then escalate case then notify manager"),

#     E2ECase("F03", "finance", "Fraud detected → lock → flag → notify",
#         "if fraud detected lock account then flag for review then notify manager"),

#     E2ECase("F04", "finance", "Account locked → notify + audit",
#         "When account is locked notify manager and create audit record"),

#     E2ECase("F05", "finance", "Payment missed → escalate + notify (parallel)",
#         "When payment is missed escalate case and notify manager"),

#     E2ECase("F06", "finance", "Payment due → remind",
#         "When payment is due send reminder"),

#     E2ECase("F07", "finance", "Fraud detected → lock + audit → notify",
#         "When fraud detected lock account and create audit record then notify manager"),

#     E2ECase("F08", "finance", "Payment due → remind → escalate",
#         "When payment is due send reminder then escalate case"),

#     E2ECase("F09", "finance", "Fraud detected → lock → notify → audit (4-step)",
#         "When fraud detected lock account then notify manager then create audit record"),

#     E2ECase("F10", "finance", "Account locked → notify + flag + audit",
#         "When account locked notify manager and flag for review then create audit record"),

#     E2ECase("F11", "finance", "Payment missed → remind + escalate → notify",
#         "When payment missed send reminder and escalate case then notify manager"),

#     E2ECase("F12", "finance", "Fraud → lock → flag → notify → audit (deep)",
#         "When fraud detected lock account then flag for review then notify manager then create audit record"),
    
#     # Additional Finance Cases (F13-F35)

# E2ECase("F13","finance","Payment missed → reminder → audit",
# "When payment missed send reminder then create audit record"),

# E2ECase("F14","finance","Payment due → reminder + notify",
# "When payment due send reminder and notify manager"),

# E2ECase("F15","finance","Fraud → lock → notify → flag",
# "When fraud detected lock account then notify manager then flag for review"),

# E2ECase("F16","finance","Fraud → lock + audit",
# "When fraud detected lock account and create audit record"),

E2ECase("F17","finance","Account locked → notify → audit",
"When account locked notify manager then create audit record"),

E2ECase("F18","finance","Payment missed → escalate → audit",
"When payment missed escalate case then create audit record"),

E2ECase("F19","finance","Payment due → reminder → notify → audit",
"When payment due send reminder then notify manager then create audit record"),

E2ECase("F20","finance","Fraud → lock → flag → audit",
"When fraud detected lock account then flag for review then create audit record"),

E2ECase("F21","finance","Payment missed → reminder → escalate",
"When payment missed send reminder then escalate case"),

E2ECase("F22","finance","Payment due → notify → audit",
"When payment due notify manager then create audit record"),

E2ECase("F23","finance","Fraud → notify → audit",
"When fraud detected notify manager then create audit record"),

E2ECase("F24","finance","Account locked → flag → audit",
"When account locked flag for review then create audit record"),

E2ECase("F25","finance","Fraud → lock → notify",
"When fraud detected lock account then notify manager"),

E2ECase("F26","finance","Payment missed → notify → audit",
"When payment missed notify manager then create audit record"),

E2ECase("F27","finance","Payment due → reminder → audit",
"When payment due send reminder then create audit record"),

E2ECase("F28","finance","Fraud → lock → audit → notify",
"When fraud detected lock account then create audit record then notify manager"),

E2ECase("F29","finance","Payment missed → reminder + notify",
"When payment missed send reminder and notify manager"),

E2ECase("F30","finance","Account locked → notify + audit",
"When account locked notify manager and create audit record"),

E2ECase("F31","finance","Fraud → flag → notify",
"When fraud detected flag for review then notify manager"),

E2ECase("F32","finance","Payment due → escalate → notify",
"When payment due escalate case then notify manager"),

E2ECase("F33","finance","Payment missed → escalate + audit",
"When payment missed escalate case and create audit record"),

E2ECase("F34","finance","Fraud → lock → flag → notify → audit",
"When fraud detected lock account then flag for review then notify manager then create audit record"),

E2ECase("F35","finance","Payment due → reminder → escalate → notify → audit",
"When payment due send reminder then escalate case then notify manager then create audit record"),
]

# ── Support (12 cases) ────────────────────────────────────────────────────────
SUPPORT_CASES = [
    E2ECase("S01", "support", "Ticket created → assign → notify×2 → close (diamond)",
        "When ticket created assign support agent then notify customer and notify manager then close case"),

    E2ECase("S02", "support", "SLA breached → alert → escalate → notify",
        "When SLA is breached send sla breach alert then escalate to tier2 then notify manager"),

    E2ECase("S03", "support", "Complaint created → ticket + notify → escalate",
        "When complaint is created create support ticket and notify manager then escalate case"),

    E2ECase("S04", "support", "Customer churned → survey + notify",
        "When customer churned send satisfaction survey and notify manager"),

    E2ECase("S05", "support", "Ticket created → assign → update → resolve",
        "When ticket is created assign support agent then send customer update then resolve ticket"),

    E2ECase("S06", "support", "Complaint → ticket → notify → resolve",
        "When complaint created create support ticket then notify manager then resolve ticket"),

    E2ECase("S07", "support", "SLA breached → alert + escalate (parallel)",
        "When SLA breached send sla breach alert and escalate to tier2"),

    E2ECase("S08", "support", "Ticket created → assign → update → close",
        "When ticket created assign support agent then send customer update then close case"),

    E2ECase("S09", "support", "Customer churned → survey → notify → audit",
        "When customer churned send satisfaction survey then notify manager then create audit record"),

    E2ECase("S10", "support", "Complaint → flag repeat → notify → escalate",
        "When complaint created flag repeat complaint then notify manager then escalate case"),

    E2ECase("S11", "support", "Ticket → assign + notify manager (parallel) → resolve",
        "When ticket created assign support agent and notify manager then resolve ticket"),

    E2ECase("S12", "support", "SLA → alert → tier2 → notify → audit",
        "When SLA breached send sla breach alert then escalate to tier2 then notify manager then create audit record"),
    # Additional Support Cases (S13-S35)

E2ECase("S13","support","Ticket → assign → notify customer",
"When ticket created assign support agent then notify customer"),

E2ECase("S14","support","Ticket → assign → notify manager",
"When ticket created assign support agent then notify manager"),

E2ECase("S15","support","Ticket → assign → update → notify",
"When ticket created assign support agent then send customer update then notify manager"),

E2ECase("S16","support","Complaint → ticket → audit",
"When complaint created create support ticket then create audit record"),

E2ECase("S17","support","Complaint → ticket → notify → audit",
"When complaint created create support ticket then notify manager then create audit record"),

E2ECase("S18","support","SLA breached → alert → audit",
"When SLA breached send sla breach alert then create audit record"),

E2ECase("S19","support","SLA breached → tier2 → audit",
"When SLA breached escalate to tier2 then create audit record"),

E2ECase("S20","support","Customer churned → survey → audit",
"When customer churned send satisfaction survey then create audit record"),

E2ECase("S21","support","Ticket → update → resolve",
"When ticket created send customer update then resolve ticket"),

E2ECase("S22","support","Complaint → notify",
"When complaint created notify manager"),

E2ECase("S23","support","Complaint → escalate",
"When complaint created escalate case"),

E2ECase("S24","support","Ticket → assign → close",
"When ticket created assign support agent then close case"),

E2ECase("S25","support","Ticket → notify customer → close",
"When ticket created notify customer then close case"),

E2ECase("S26","support","SLA breached → notify manager",
"When SLA breached notify manager"),

E2ECase("S27","support","Complaint → ticket → resolve",
"When complaint created create support ticket then resolve ticket"),

E2ECase("S28","support","Ticket → assign + notify customer",
"When ticket created assign support agent and notify customer"),

E2ECase("S29","support","Ticket → assign + notify manager",
"When ticket created assign support agent and notify manager"),

E2ECase("S30","support","Customer churned → notify manager",
"When customer churned notify manager"),

E2ECase("S31","support","Complaint → audit",
"When complaint created create audit record"),

E2ECase("S32","support","Ticket → update → audit",
"When ticket created send customer update then create audit record"),

E2ECase("S33","support","SLA breached → alert → notify → audit",
"When SLA breached send sla breach alert then notify manager then create audit record"),

E2ECase("S34","support","Complaint → ticket → notify → escalate → audit",
"When complaint created create support ticket then notify manager then escalate case then create audit record"),

E2ECase("S35","support","Ticket → assign → update → notify → resolve",
"When ticket created assign support agent then send customer update then notify manager then resolve ticket"),
]

# ── Health (11 cases) ─────────────────────────────────────────────────────────
HEALTH_CASES = [
    E2ECase("H01", "health", "Critical vitals → alert → escalate → notify",
        "When critical vitals detected alert care team then escalate to specialist then notify manager"),

    E2ECase("H02", "health", "Medication overdue → remind + notify",
        "When medication is overdue send medication reminder then notify manager"),

    E2ECase("H03", "health", "Patient discharged → instructions + audit",
        "When patient is discharged send discharge instructions and create audit record"),

    E2ECase("H04", "health", "Critical vitals → alert + notify + escalate (3-way)",
        "When critical vitals detected alert care team and notify manager and escalate to specialist"),

    E2ECase("H05", "health", "Medication overdue → remind → flag high risk",
        "When medication overdue send medication reminder then flag high risk patient"),

    E2ECase("H06", "health", "Patient discharged → instructions → notify → audit",
        "When patient discharged send discharge instructions then notify manager then create audit record"),

    E2ECase("H07", "health", "Critical vitals → alert → emergency protocol",
        "When critical vitals detected alert care team then trigger emergency protocol"),

    E2ECase("H08", "health", "Medication overdue → remind + flag (parallel)",
        "When medication overdue send medication reminder and flag high risk patient"),

    E2ECase("H09", "health", "Patient discharged → instructions + wellness check",
        "When patient discharged send discharge instructions and send wellness check"),

    E2ECase("H10", "health", "Critical vitals → alert + escalate → notify + audit",
        "When critical vitals detected alert care team and escalate to specialist then notify manager and create audit record"),

    E2ECase("H11", "health", "Medication overdue → remind → notify → audit (chain)",
        "When medication overdue send medication reminder then notify manager then create audit record"),
    # Additional Health Cases (H12-H30)

E2ECase("H12","health","Critical vitals → alert → audit",
"When critical vitals detected alert care team then create audit record"),

E2ECase("H13","health","Critical vitals → alert + notify",
"When critical vitals detected alert care team and notify manager"),

E2ECase("H14","health","Medication overdue → audit",
"When medication overdue create audit record"),

E2ECase("H15","health","Medication overdue → notify",
"When medication overdue notify manager"),

E2ECase("H16","health","Patient discharged → instructions → wellness check",
"When patient discharged send discharge instructions then send wellness check"),

E2ECase("H17","health","Patient discharged → instructions → audit",
"When patient discharged send discharge instructions then create audit record"),

E2ECase("H18","health","Critical vitals → specialist → audit",
"When critical vitals detected escalate to specialist then create audit record"),

E2ECase("H19","health","Medication overdue → reminder + audit",
"When medication overdue send medication reminder and create audit record"),

E2ECase("H20","health","Patient discharged → notify manager",
"When patient discharged notify manager"),

E2ECase("H21","health","Critical vitals → emergency protocol",
"When critical vitals detected trigger emergency protocol"),

E2ECase("H22","health","Medication overdue → flag patient",
"When medication overdue flag high risk patient"),

E2ECase("H23","health","Patient discharged → wellness check",
"When patient discharged send wellness check"),

E2ECase("H24","health","Critical vitals → alert → specialist",
"When critical vitals detected alert care team then escalate to specialist"),

E2ECase("H25","health","Medication overdue → reminder → notify",
"When medication overdue send medication reminder then notify manager"),

E2ECase("H26","health","Patient discharged → audit",
"When patient discharged create audit record"),

E2ECase("H27","health","Critical vitals → notify → audit",
"When critical vitals detected notify manager then create audit record"),

E2ECase("H28","health","Medication overdue → reminder → audit → notify",
"When medication overdue send medication reminder then create audit record then notify manager"),

E2ECase("H29","health","Patient discharged → instructions → notify",
"When patient discharged send discharge instructions then notify manager"),

E2ECase("H30","health","Critical vitals → alert → specialist → notify → audit",
"When critical vitals detected alert care team then escalate to specialist then notify manager then create audit record"),
    
]

# ── Edge / Boundary (expect failure) ─────────────────────────────────────────
EDGE_CASES = [
    E2ECase("E01", "finance", "No trigger present",
        "Just send a reminder to the customer",
        expect_success=False),

    E2ECase("E02", "support", "Gibberish input",
        "xkzpq brflt vwxmn zzz",
        expect_success=False),

    E2ECase("E03", "health", "Unknown trigger",
        "When spaceship launched alert care team",
        expect_success=False),
]

ALL_CASES = FINANCE_CASES + SUPPORT_CASES + HEALTH_CASES + EDGE_CASES
DOMAIN_MAP = {
    "finance": FINANCE_CASES,
    "support": SUPPORT_CASES,
    "health": HEALTH_CASES,
    "edge": EDGE_CASES,
}


def build_compiler():
    return WorkflowCompilerService(
        dsl_generator=DSLGenerator(),
        rule_parser=RuleParser(),
        ast_builder=WorkflowASTBuilder(),
        ast_validator=ASTValidator(),
        workflow_compiler=WorkflowComplier(),
    )


def run_case(case: E2ECase) -> bool:
    print(f"\n{'─' * 70}")
    print(f"  [{case.id}] {case.description}")
    print(f"  Domain: {case.domain}")
    print(f"  Input:  \"{case.user_request}\"")
    print(f"{'─' * 70}")

    db = SessionLocal()
    try:
        # 1 — Catalog
        catalog = CatalogMatcher(
            TriggerDefinitionRepository(db),
            ActionDefinitionRepository(db),
        ).match(case.user_request)

        print(f"  Catalog  triggers={catalog.trigger_names}  actions={catalog.action_names}")

        # 2 — Suitability
        suit = SuitabilityAgent().evaluate(
            catalog.workflow_type,
            catalog.trigger_names,
            catalog.action_names,
        )
        if not suit.supported:
            if not case.expect_success:
                print(f"  ✅ PASSED (expected rejection: {suit.reason})")
                return True
            print(f"  ❌ FAILED — suitability rejected: {suit.reason}")
            return False

        # 3 — Prompt + LLM
        context = PromptContext(
            workflow_type=catalog.workflow_type,
            triggers=[t.name for t in catalog.matched_triggers],
            actions=[a.name for a in catalog.matched_actions],
            user_request=case.user_request,
        )
        prompt_result = PromptBuilder().build(context)
        llm_result = LLMManager().generate(prompt_result.prompt)

        if not llm_result["success"]:
            if not case.expect_success:
                print(f"  ✅ PASSED (expected LLM failure)")
                return True
            print(f"  ❌ FAILED — LLM error: {llm_result.get('error')}")
            return False

        print(f"  LLM OK  provider={llm_result.get('provider', 'unknown')}")

        # 4 — Parse + validate
        workflow_json = WorkflowResponseParser().parse(llm_result["output"])
        schema_r = WorkflowSchemaValidator().validate(workflow_json)
        if not schema_r.valid:
            if not case.expect_success:
                print(f"  ✅ PASSED (expected schema fail)")
                return True
            print(f"  ❌ FAILED — schema: {schema_r.errors}")
            return False

        wf_r = WorkflowValidator().validate(workflow_json)
        if not wf_r.valid:
            if not case.expect_success:
                print(f"  ✅ PASSED (expected validation fail)")
                return True
            print(f"  ❌ FAILED — validation: {wf_r.errors}")
            return False

        # 5 — Compile
        compile_result = build_compiler().compile(catalog.workflow_type, workflow_json)
        compiled = compile_result["compiled"]
        print(f"  DSL steps: {len(compiled['steps'])}")

        # 6 — Save
        saved = WorkflowPersistenceService().save(
            db=db,
            name=f"e2e-{case.id.lower()}",
            domain=case.domain,
            user_request=case.user_request,
            compile_result=compile_result,
        )
        workflow_id = saved["workflow_id"]
        print(f"  Saved  workflow_id={workflow_id}")

        # 7 — Execute
        resp = requests.post(
            f"{BASE_URL}/api/execute/",
            json={"workflow_id": workflow_id, "entity_id": f"e2e-{case.id.lower()}"},
            timeout=10,
        )
        resp.raise_for_status()
        body = resp.json()

        if not body.get("success"):
            print(f"  ❌ FAILED — execute returned success=False: {body}")
            return False

        workflow_execution_id = body["workflow_execution_id"]
        print(f"  Queued  execution_id={workflow_execution_id}  polling", end="", flush=True)

        # 8 — Poll
        deadline = time.time() + POLL_TIMEOUT
        final_status = None
        while time.time() < deadline:
            db.expire_all()
            execution = db.query(WorkflowExecution).filter(
                WorkflowExecution.id == workflow_execution_id
            ).first()
            if execution:
                final_status = execution.status
                print(f" {final_status}", end="", flush=True)
                if final_status in ("COMPLETED", "FAILED", "DLQ"):
                    break
            time.sleep(POLL_INTERVAL)
        print()

        if final_status == "COMPLETED":
            if case.expect_success:
                print(f"  ✅ PASSED")
                return True
            else:
                print(f"  ❌ FAILED — expected failure but got COMPLETED")
                return False
        else:
            if not case.expect_success:
                print(f"  ✅ PASSED (expected failure, got {final_status})")
                return True
            print(f"  ❌ FAILED — final status: {final_status}")
            return False

    except Exception as e:
        import traceback
        if not case.expect_success:
            print(f"  ✅ PASSED (expected exception: {type(e).__name__}: {e})")
            return True
        print(f"  ❌ EXCEPTION — {type(e).__name__}: {e}")
        print(traceback.format_exc())
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Full E2E test suite")
    parser.add_argument("--id", help="Run single case (e.g. F01)")
    parser.add_argument("--domain", choices=["finance", "support", "health", "edge"],
                        help="Run all cases for a domain")
    parser.add_argument("--stop-on-fail", action="store_true")
    args = parser.parse_args()

    if args.id:
        cases = [c for c in ALL_CASES if c.id == args.id.upper()]
        if not cases:
            print(f"No case '{args.id}'")
            sys.exit(1)
    elif args.domain:
        cases = DOMAIN_MAP[args.domain]
    else:
        cases = ALL_CASES

    print("\n" + "=" * 70)
    print(f"E2E FULL PIPELINE TEST — {len(cases)} cases")
    print("=" * 70)

    passed = failed = 0
    for case in cases:
        ok = run_case(case)
        if ok:
            passed += 1
        else:
            failed += 1
            if args.stop_on_fail:
                print("\n[--stop-on-fail] Stopping.")
                break

    print("\n" + "=" * 70)
    print(f"TOTAL: {passed+failed}   ✅ PASSED: {passed}   ❌ FAILED: {failed}")
    print("=" * 70)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
