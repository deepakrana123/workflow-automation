"""
scripts/test_semantic_e2e.py

Full end-to-end test: semantic search → LLM → compile → save → execute → COMPLETED

All 20 cases use only triggers and actions confirmed present in the DB.
Target: 60-70% pass rate → ready for deployment.

Requirements:
    docker-compose up   (all services including worker)
    backfill_embeddings must have been run

Run:
    .venv\\Scripts\\python.exe scripts/test_semantic_e2e.py
    .venv\\Scripts\\python.exe scripts/test_semantic_e2e.py --id F01
    .venv\\Scripts\\python.exe scripts/test_semantic_e2e.py --domain finance
    .venv\\Scripts\\python.exe scripts/test_semantic_e2e.py --stop-on-fail --verbose
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
from app.semantic.semantic_catalog_retriever import SemanticCatalogRetriever
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


# ── 20 cases using only confirmed DB triggers + actions ───────────────────────

CASES = [

    # ── Finance — payment_missed trigger ──────────────────────────────────────
    E2ECase("F01", "finance",
        "invoice unpaid → escalate + notify manager",
        "invoice still unpaid escalate the case and tell the manager"),

    E2ECase("F02", "finance",
        "payment missed → escalate + audit",
        "payment was not received escalate case and create audit trail"),

    E2ECase("F03", "finance",
        "payment missed → notify manager",
        "payment was not received tell the manager right away"),

    # ── Finance — fraud_detected trigger ──────────────────────────────────────
    E2ECase("F04", "finance",
        "suspicious activity → flag + notify",
        "suspicious account activity mark for investigation and alert supervisor"),

    E2ECase("F05", "finance",
        "fraud detected → freeze account then audit",
        "fraudulent transaction detected freeze the account then log compliance record"),

    E2ECase("F06", "finance",
        "fraud → flag then notify manager",
        "fraud detected mark for investigation then inform the manager"),

    # ── Finance — payment_due trigger ─────────────────────────────────────────
    E2ECase("F07", "finance",
        "bill past due → warn customer then escalate",
        "bill is past due send payment warning to customer then raise the case to higher level"),

    # ── Support — ticket_created trigger ──────────────────────────────────────
    E2ECase("S01", "support",
        "new issue opened → assign agent then update customer",
        "new support request submitted route ticket to an agent then inform customer about update"),

    E2ECase("S02", "support",
        "ticket created → assign + notify manager",
        "new issue was opened assign employee to ticket and alert supervisor"),

    E2ECase("S03", "support",
        "ticket → assign → update → resolve",
        "ticket created assign support agent then send customer update then resolve ticket"),

    # ── Support — complaint_created trigger ───────────────────────────────────
    E2ECase("S04", "support",
        "complaint filed → ticket + notify",
        "complaint filed by customer create support ticket and alert supervisor"),

    E2ECase("S05", "support",
        "grievance → assign then escalate",
        "customer raised a grievance assign employee to ticket then raise the case to higher level"),

    # ── Support — sla_breached trigger ────────────────────────────────────────
    E2ECase("S06", "support",
        "response time exceeded → alert + escalate tier2",
        "response time exceeded send sla breach alert and push to tier two team"),

    E2ECase("S07", "support",
        "SLA breached → escalate then notify manager",
        "SLA breached escalate to tier2 then notify manager"),

    # ── Support — customer_churned trigger ────────────────────────────────────
    E2ECase("S08", "support",
        "customer cancelled → survey + notify",
        "client stopped using service send customer satisfaction form and tell the manager"),

    # ── Health — critical_vitals trigger ──────────────────────────────────────
    E2ECase("H01", "health",
        "vital signs critical → alert team then refer specialist",
        "vital signs critical alert the medical team then refer patient to specialist"),

    E2ECase("H02", "health",
        "patient deteriorated → emergency protocol + notify",
        "patient condition deteriorated activate emergency response then notify care staff immediately"),

    E2ECase("H03", "health",
        "critical vitals → 3-way parallel response",
        "vital signs critical alert care team and notify manager and escalate to specialist"),

    # ── Health — medication_overdue trigger ───────────────────────────────────
    E2ECase("H04", "health",
        "prescription overdue → pill reminder then notify",
        "prescription overdue send pill reminder to patient then notify manager"),

    # ── Health — patient_discharged trigger ───────────────────────────────────
    E2ECase("H05", "health",
        "patient left hospital → discharge instructions + audit",
        "patient left the hospital send home care instructions and log compliance record"),
]

DOMAIN_MAP = {
    "finance": [c for c in CASES if c.domain == "finance"],
    "support": [c for c in CASES if c.domain == "support"],
    "health":  [c for c in CASES if c.domain == "health"],
}


def build_compiler():
    return WorkflowCompilerService(
        dsl_generator=DSLGenerator(),
        rule_parser=RuleParser(),
        ast_builder=WorkflowASTBuilder(),
        ast_validator=ASTValidator(),
        workflow_compiler=WorkflowComplier(),
    )


def run_case(case: E2ECase, verbose: bool) -> bool:
    print(f"\n{'─' * 70}")
    print(f"  [{case.id}] {case.description}")
    print(f"  Input : \"{case.user_request}\"")
    print(f"{'─' * 70}")

    db = SessionLocal()
    try:
        # 1 — Catalog (keyword + semantic)
        matcher = CatalogMatcher(
            trigger_repository=TriggerDefinitionRepository(db),
            action_repository=ActionDefinitionRepository(db),
            semantic_retriever=SemanticCatalogRetriever(),
        )
        catalog = matcher.match(db, case.user_request)
        print(f"  [1] triggers={catalog.trigger_names}  actions={catalog.action_names}")

        # 2 — Suitability
        suit = SuitabilityAgent().evaluate(
            catalog.workflow_type,
            catalog.trigger_names,
            catalog.action_names,
        )
        if not suit.supported:
            print(f"  ❌ Suitability rejected: {suit.reason}")
            return False
        print(f"  [2] Suitability ✓  type={catalog.workflow_type}")

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
            print(f"  ❌ LLM failed: {llm_result.get('error')}")
            return False
        print(f"  [3] LLM ✓  provider={llm_result.get('provider', 'unknown')}")

        if verbose:
            print(f"      {llm_result['output'][:200]}")

        # 4 — Parse + validate
        workflow_json = WorkflowResponseParser().parse(llm_result["output"])
        schema_r = WorkflowSchemaValidator().validate(workflow_json)
        if not schema_r.valid:
            print(f"  ❌ Schema: {schema_r.errors}")
            return False
        wf_r = WorkflowValidator().validate(workflow_json)
        if not wf_r.valid:
            print(f"  ❌ Workflow: {wf_r.errors}")
            return False
        print(f"  [4] Validation ✓")

        # 5 — Compile
        compile_result = build_compiler().compile(catalog.workflow_type, workflow_json)
        compiled = compile_result["compiled"]
        steps = compiled.get("steps", [])
        print(f"  [5] Compiled  steps={len(steps)}")
        if verbose:
            for s in steps:
                print(f"       @{s['id']}: {s['action']}  deps={s['depends_on']}")

        # 6 — Save
        saved = WorkflowPersistenceService().save(
            db=db,
            name=f"e2e-{case.id.lower()}",
            domain=case.domain,
            user_request=case.user_request,
            compile_result=compile_result,
        )
        workflow_id = saved["workflow_id"]
        print(f"  [6] Saved  workflow_id={workflow_id}")

        # 7 — Execute
        resp = requests.post(
            f"{BASE_URL}/api/execute/",
            json={"workflow_id": workflow_id, "entity_id": f"e2e-{case.id.lower()}"},
            timeout=10,
        )
        resp.raise_for_status()
        body = resp.json()
        if not body.get("success"):
            print(f"  ❌ Execute: {body}")
            return False

        execution_id = body["workflow_execution_id"]
        print(f"  [7] Queued  exec_id={execution_id}  polling", end="", flush=True)

        # 8 — Poll
        deadline = time.time() + POLL_TIMEOUT
        final_status = None
        while time.time() < deadline:
            db.expire_all()
            ex = db.query(WorkflowExecution).filter(
                WorkflowExecution.id == execution_id
            ).first()
            if ex:
                final_status = ex.status
                print(f" {final_status}", end="", flush=True)
                if final_status in ("COMPLETED", "FAILED", "DLQ"):
                    break
            time.sleep(POLL_INTERVAL)
        print()

        if final_status == "COMPLETED":
            print(f"  ✅ PASSED")
            return True
        else:
            print(f"  ❌ FAILED — status: {final_status}")
            return False

    except Exception as e:
        import traceback
        print(f"  ❌ EXCEPTION — {type(e).__name__}: {e}")
        if verbose:
            print(traceback.format_exc())
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Semantic E2E test — deployment readiness")
    parser.add_argument("--id",     help="Run single case (e.g. F01)")
    parser.add_argument("--domain", choices=["finance", "support", "health"])
    parser.add_argument("--stop-on-fail", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    cases = CASES
    if args.id:
        cases = [c for c in CASES if c.id == args.id.upper()]
        if not cases:
            print(f"No case '{args.id}'")
            sys.exit(1)
    elif args.domain:
        cases = DOMAIN_MAP[args.domain]

    print("\n" + "=" * 70)
    print(f"SEMANTIC E2E — {len(cases)} cases  (target: 60-70% to deploy)")
    print("=" * 70)

    passed = failed = 0
    for case in cases:
        ok = run_case(case, args.verbose)
        if ok:
            passed += 1
        else:
            failed += 1
            if args.stop_on_fail:
                print("\n[--stop-on-fail] Stopping.")
                break

    total = passed + failed
    pct = int(passed / total * 100) if total else 0
    deploy_ready = "✅ DEPLOY READY" if pct >= 60 else "❌ NOT READY"

    print("\n" + "=" * 70)
    print(f"TOTAL: {total}   ✅ PASSED: {passed}   ❌ FAILED: {failed}   ({pct}%)")
    print(f"STATUS: {deploy_ready}")
    print("=" * 70)
    sys.exit(0 if pct >= 60 else 1)


if __name__ == "__main__":
    main()
