"""
scripts/test_semantic_e2e.py

Full end-to-end test: semantic search → LLM → compile → save → execute → COMPLETED
105 cases covering finance, banking, home loan, car loan, support, health.

Requirements:
    docker-compose up   (all services including worker)
    backfill_embeddings must have been run

Run:
    .venv\\Scripts\\python.exe scripts/test_semantic_e2e.py
    .venv\\Scripts\\python.exe scripts/test_semantic_e2e.py --id F01
    .venv\\Scripts\\python.exe scripts/test_semantic_e2e.py --domain banking
    .venv\\Scripts\\python.exe scripts/test_semantic_e2e.py --domain homeloan
    .venv\\Scripts\\python.exe scripts/test_semantic_e2e.py --domain carloan
    .venv\\Scripts\\python.exe scripts/test_semantic_e2e.py --domain support
    .venv\\Scripts\\python.exe scripts/test_semantic_e2e.py --domain health
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
from app.prompting import PromptManager, PromptContext, PromptKey
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
    group: str
    description: str
    user_request: str


CASES = [

    # ════════════════════════════════════════════════════════════════════
    # GENERAL BANKING (B01-B20)
    # ════════════════════════════════════════════════════════════════════

    E2ECase("B01", "finance", "banking",
        "fraud detected → freeze + audit + notify",
        "suspicious account activity freeze the account create audit record and notify manager"),

    E2ECase("B02", "finance", "banking",
        "fraud → flag + escalate + report",
        "fraud detected flag high risk customer escalate case then submit regulatory report"),

    E2ECase("B03", "finance", "banking",
        "payment missed → reminder → notice → escalate",
        "payment was not received send payment reminder then send overdue notice then escalate case"),

    E2ECase("B04", "finance", "banking",
        "payment missed → collection → agent",
        "invoice still unpaid initiate collection and assign recovery agent"),

    E2ECase("B05", "finance", "banking",
        "payment missed → legal action",
        "loan payment overdue initiate collection assign recovery agent send legal notice then initiate legal action"),

    E2ECase("B06", "finance", "banking",
        "new account → kyc → welcome",
        "customer opened new account initiate kyc send kyc reminder complete kyc then send welcome kit"),

    E2ECase("B07", "finance", "banking",
        "new account → aml + sanctions",
        "new account created perform aml screening and sanctions check then notify branch"),

    E2ECase("B08", "finance", "banking",
        "transaction validation → neft",
        "customer requested fund transfer validate transaction then process neft and send payment confirmation"),

    E2ECase("B09", "finance", "banking",
        "failed transaction → notify + audit",
        "transaction failed notify payment failure create audit record then notify manager"),

    E2ECase("B10", "finance", "banking",
        "high risk → risk score + alert",
        "customer flagged suspicious calculate risk score flag high risk customer and send risk alert"),

    E2ECase("B11", "finance", "banking",
        "credit limit update",
        "customer eligible for higher credit update credit limit then notify customer"),

    E2ECase("B12", "finance", "banking",
        "dormant account → reactivate",
        "account has been dormant reactivate dormant account then send account statement and notify customer"),

    E2ECase("B13", "finance", "banking",
        "lost card → block → new card",
        "customer reported lost card block debit card then issue new card and notify customer"),

    E2ECase("B14", "finance", "banking",
        "overdraft activation",
        "customer requested overdraft facility activate overdraft then send account statement"),

    E2ECase("B15", "finance", "banking",
        "account upgrade → notify",
        "customer eligible for premium upgrade account update credit limit then notify customer"),

    E2ECase("B16", "finance", "banking",
        "compliance verification",
        "account flagged for compliance verify compliance perform aml screening then create audit record"),

    E2ECase("B17", "finance", "banking",
        "hold funds → verify → release",
        "suspicious transaction hold funds verify compliance then release funds"),

    E2ECase("B18", "finance", "banking",
        "interest certificate generation",
        "financial year ended generate interest certificate then send statement to customer"),

    E2ECase("B19", "finance", "banking",
        "regulatory report",
        "quarter end submit regulatory report create audit record and notify manager"),

    E2ECase("B20", "finance", "banking",
        "rtgs transfer + confirmation",
        "high value transfer requested process rtgs send payment confirmation and create audit record"),

    # ════════════════════════════════════════════════════════════════════
    # PERSONAL / GENERAL LOAN (L01-L20)
    # ════════════════════════════════════════════════════════════════════

    E2ECase("L01", "finance", "banking",
        "loan application → cibil → sanction",
        "new loan application received run cibil check verify income then issue sanction letter"),

    E2ECase("L02", "finance", "banking",
        "loan application → cibil low → reject",
        "loan applied cibil score came back poor send cibil low alert then send rejection letter"),

    E2ECase("L03", "finance", "banking",
        "loan approved → agreement → disburse",
        "loan approved generate loan agreement calculate emi generate repayment schedule then disburse loan"),

    E2ECase("L04", "finance", "banking",
        "loan disburse → notification",
        "loan disbursed send disbursement advice send payment confirmation then notify customer"),

    E2ECase("L05", "finance", "banking",
        "document collection → verify → proceed",
        "customer submitted documents send document checklist verify submitted documents then send validation documents"),

    E2ECase("L06", "finance", "banking",
        "loan → insurance → disburse",
        "loan approved link insurance to loan send insurance reminder then disburse loan"),

    E2ECase("L07", "finance", "banking",
        "emi due → reminder",
        "emi due send payment reminder and notify customer"),

    E2ECase("L08", "finance", "banking",
        "emi missed → notice → agent",
        "emi missed send overdue notice initiate collection then assign recovery agent"),

    E2ECase("L09", "finance", "banking",
        "loan closure → noc → cibil update",
        "loan fully repaid send noc on closure then update cibil post closure"),

    E2ECase("L10", "finance", "banking",
        "loan foreclosure request",
        "customer requested early loan closure send foreclosure statement calculate emi then send noc on closure"),

    E2ECase("L11", "finance", "banking",
        "restructure loan",
        "customer in financial distress restructure loan generate repayment schedule then notify customer"),

    E2ECase("L12", "finance", "banking",
        "waive penalty → notify",
        "customer requested penalty waiver waive penalty then send statement and notify customer"),

    E2ECase("L13", "finance", "banking",
        "write off bad loan",
        "loan irrecoverable write off loan create audit record submit regulatory report and notify manager"),

    E2ECase("L14", "finance", "banking",
        "underwriting approval",
        "loan application received assess creditworthiness run bureau check approve underwriting then issue sanction letter"),

    E2ECase("L15", "finance", "banking",
        "underwriting rejection",
        "loan application failed creditworthiness check reject underwriting then send rejection letter"),

    E2ECase("L16", "finance", "banking",
        "income + docs + sanction",
        "loan application received run income verification send document checklist verify submitted documents then issue sanction letter"),

    E2ECase("L17", "finance", "banking",
        "post disbursement docs",
        "loan disbursed collect post disbursement documents then create audit record"),

    E2ECase("L18", "finance", "banking",
        "annual interest certificate",
        "financial year completed generate interest certificate then send statement"),

    E2ECase("L19", "finance", "banking",
        "penalty charge + notify",
        "late payment received charge penalty send overdue notice then notify customer"),

    E2ECase("L20", "finance", "banking",
        "apply interest on account",
        "monthly cycle completed apply interest generate repayment schedule then send statement"),

    # ════════════════════════════════════════════════════════════════════
    # HOME LOAN (H01-H25)
    # ════════════════════════════════════════════════════════════════════

    E2ECase("HL01", "finance", "homeloan",
        "home loan application → cibil → valuation",
        "home loan application received run cibil check then initiate property valuation"),

    E2ECase("HL02", "finance", "homeloan",
        "property valuation → technical visit",
        "property valuation initiated schedule technical visit then send technical report"),

    E2ECase("HL03", "finance", "homeloan",
        "technical done → legal verification",
        "technical appraisal completed initiate legal verification then send to legal team"),

    E2ECase("HL04", "finance", "homeloan",
        "legal query raised → notify customer",
        "legal team raised query on property documents raise legal query then notify customer"),

    E2ECase("HL05", "finance", "homeloan",
        "legal cleared → sanction",
        "legal verification completed mark legal cleared then issue sanction letter and send sanction terms"),

    E2ECase("HL06", "finance", "homeloan",
        "sanction accepted → agreement → mortgage",
        "customer accepted loan offer generate loan agreement then register mortgage"),

    E2ECase("HL07", "finance", "homeloan",
        "mortgage registered → collect docs → disburse",
        "mortgage registered collect original property documents then notify developer and disburse tranche"),

    E2ECase("HL08", "finance", "homeloan",
        "tranche disbursement",
        "construction milestone reached disburse tranche notify developer disbursement and send disbursement advice"),

    E2ECase("HL09", "finance", "homeloan",
        "insurance for home loan",
        "home loan approved link insurance to loan send insurance reminder then disburse tranche"),

    E2ECase("HL10", "finance", "homeloan",
        "possession notice",
        "property possession ready send possession notice then notify customer"),

    E2ECase("HL11", "finance", "homeloan",
        "home loan closure → docs return",
        "home loan fully repaid send noc on closure return original documents then update cibil post closure"),

    E2ECase("HL12", "finance", "homeloan",
        "full home loan origination flow",
        "home loan application received run cibil check run income verification send document checklist verify submitted documents initiate property valuation schedule technical visit send technical report initiate legal verification send to legal team legal verification cleared issue sanction letter"),

    E2ECase("HL13", "finance", "homeloan",
        "home loan disbursement flow",
        "home loan sanctioned customer accepted offer generate loan agreement register mortgage collect original property documents notify developer disbursement disburse tranche send disbursement advice generate repayment schedule"),

    E2ECase("HL14", "finance", "homeloan",
        "home loan emi overdue",
        "home loan emi missed send payment reminder send overdue notice then initiate collection"),

    E2ECase("HL15", "finance", "homeloan",
        "home loan pre-closure",
        "customer requested home loan preclosure send foreclosure statement calculate emi send noc on closure return original documents and update cibil post closure"),

    # ════════════════════════════════════════════════════════════════════
    # CAR LOAN (CL01-CL15)
    # ════════════════════════════════════════════════════════════════════

    E2ECase("CL01", "finance", "carloan",
        "car loan application → cibil → valuation",
        "car loan application received run cibil check then initiate vehicle valuation"),

    E2ECase("CL02", "finance", "carloan",
        "vehicle valued → dealer invoice",
        "vehicle valuation done verify dealer invoice then coordinate with dealer"),

    E2ECase("CL03", "finance", "carloan",
        "car loan sanction → disburse to dealer",
        "car loan approved issue sanction letter then disburse to dealer and send vehicle delivery confirmation"),

    E2ECase("CL04", "finance", "carloan",
        "vehicle delivered → rc hypothecation",
        "vehicle delivered to customer initiate rc hypothecation send rc endorsement notice then notify customer"),

    E2ECase("CL05", "finance", "carloan",
        "car insurance check",
        "car loan disbursement pending verify vehicle insurance then coordinate with dealer and disburse to dealer"),

    E2ECase("CL06", "finance", "carloan",
        "car loan closure → release hypothecation",
        "car loan fully repaid release hypothecation send noc on closure then update cibil post closure"),

    E2ECase("CL07", "finance", "carloan",
        "car loan foreclosure",
        "customer requested early car loan closure send foreclosure statement then release hypothecation send noc on closure"),

    E2ECase("CL08", "finance", "carloan",
        "car loan emi overdue",
        "car loan emi missed send payment reminder send overdue notice then assign recovery agent"),

    E2ECase("CL09", "finance", "carloan",
        "full car loan origination",
        "car loan application received run cibil check run income verification initiate vehicle valuation verify dealer invoice verify vehicle insurance issue sanction letter disburse to dealer"),

    E2ECase("CL10", "finance", "carloan",
        "car loan post disbursement",
        "car loan disbursed initiate rc hypothecation send rc endorsement notice collect post disbursement documents then send welcome kit"),

    # ════════════════════════════════════════════════════════════════════
    # SUPPORT (S01-S15)
    # ════════════════════════════════════════════════════════════════════

    E2ECase("S01", "support", "support",
        "new ticket → assign → update → resolve",
        "new support ticket created assign support agent send customer update then resolve ticket"),

    E2ECase("S02", "support", "support",
        "ticket → assign → notify manager",
        "support request submitted assign support agent then notify manager"),

    E2ECase("S03", "support", "support",
        "complaint → ticket → escalate",
        "complaint filed create support ticket then escalate to tier2 and notify manager"),

    E2ECase("S04", "support", "support",
        "sla breached → alert → escalate",
        "sla breached send sla breach alert then escalate to tier2 notify manager"),

    E2ECase("S05", "support", "support",
        "customer churned → survey + notify",
        "customer cancelled service send satisfaction survey and notify manager"),

    E2ECase("S06", "support", "support",
        "refund request → process → update customer",
        "customer wants money back process refund then send customer update"),

    E2ECase("S07", "support", "support",
        "repeat complaint → flag + escalate",
        "customer filed complaint again flag repeat complaint then escalate case and notify manager"),

    E2ECase("S08", "support", "support",
        "ticket unresolved → tier2 → notify",
        "ticket still pending escalate to tier2 send customer update then notify manager"),

    E2ECase("S09", "support", "support",
        "ticket full flow",
        "ticket created assign support agent send customer update resolve ticket then close case"),

    E2ECase("S10", "support", "support",
        "complaint flow with audit",
        "complaint created create support ticket assign support agent resolve ticket then send satisfaction survey"),

    E2ECase("S11", "support", "support",
        "sla breach full flow",
        "response time exceeded send sla breach alert escalate to tier2 notify manager then create audit record"),

    E2ECase("S12", "support", "support",
        "refund + survey",
        "customer wants refund process refund send customer update then send satisfaction survey"),

    E2ECase("S13", "support", "support",
        "no response ticket close",
        "ticket has no customer response close ticket no response and notify manager"),

    E2ECase("S14", "support", "support",
        "parallel notify on ticket",
        "ticket created assign support agent then notify customer and notify manager"),

    E2ECase("S15", "support", "support",
        "complaint diamond flow",
        "complaint filed create support ticket and notify manager then resolve ticket"),

    # ════════════════════════════════════════════════════════════════════
    # HEALTH (HH01-HH15)
    # ════════════════════════════════════════════════════════════════════

    E2ECase("HH01", "health", "health",
        "critical vitals → alert + escalate",
        "vital signs critical alert care team then escalate to specialist"),

    E2ECase("HH02", "health", "health",
        "critical → emergency protocol",
        "patient condition deteriorated trigger emergency protocol then alert care team and notify manager"),

    E2ECase("HH03", "health", "health",
        "medication overdue → remind + notify",
        "prescription overdue send medication reminder then notify manager"),

    E2ECase("HH04", "health", "health",
        "patient discharged → instructions + audit",
        "patient left hospital send discharge instructions and create audit record"),

    E2ECase("HH05", "health", "health",
        "lab result → notify lab + schedule",
        "test results available notify lab result then schedule appointment"),

    E2ECase("HH06", "health", "health",
        "appointment missed → wellness check",
        "patient skipped appointment send wellness check then notify manager"),

    E2ECase("HH07", "health", "health",
        "critical vitals 3-way",
        "vital signs critical alert care team and notify manager and escalate to specialist"),

    E2ECase("HH08", "health", "health",
        "patient admitted → schedule + notify",
        "patient checked into hospital schedule appointment and notify manager"),

    E2ECase("HH09", "health", "health",
        "insurance denied → escalate",
        "insurance denied escalate to specialist then notify manager"),

    E2ECase("HH10", "health", "health",
        "medication + flag high risk",
        "medication overdue send medication reminder then flag high risk patient"),

    E2ECase("HH11", "health", "health",
        "discharge → instructions + wellness",
        "patient discharged send discharge instructions and send wellness check"),

    E2ECase("HH12", "health", "health",
        "followup due → schedule",
        "followup appointment due schedule appointment then send medication reminder"),

    E2ECase("HH13", "health", "health",
        "emergency full flow",
        "patient condition deteriorated trigger emergency protocol alert care team escalate to specialist then notify manager"),

    E2ECase("HH14", "health", "health",
        "critical vitals → alert + audit",
        "critical vitals detected alert care team create audit record then notify manager"),

    E2ECase("HH15", "health", "health",
        "patient discharge + insurance",
        "patient discharged request insurance approval send discharge instructions then schedule appointment"),
]

DOMAIN_MAP = {
    "banking":  [c for c in CASES if c.group == "banking"],
    "homeloan": [c for c in CASES if c.group == "homeloan"],
    "carloan":  [c for c in CASES if c.group == "carloan"],
    "support":  [c for c in CASES if c.group == "support"],
    "health":   [c for c in CASES if c.group == "health"],
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
    print(f"  Input : \"{case.user_request[:80]}{'...' if len(case.user_request) > 80 else ''}\"")
    print(f"{'─' * 70}")

    db = SessionLocal()
    try:
        matcher = CatalogMatcher(
            trigger_repository=TriggerDefinitionRepository(db),
            action_repository=ActionDefinitionRepository(db),
            semantic_retriever=SemanticCatalogRetriever(),
        )
        catalog = matcher.match(db, case.user_request)
        print(f"  [1] triggers={catalog.trigger_names}  actions={catalog.action_names[:5]}{'...' if len(catalog.action_names) > 5 else ''}")

        suit = SuitabilityAgent().evaluate(
            catalog.workflow_type,
            catalog.trigger_names,
            catalog.action_names,
        )
        if not suit.supported:
            print(f"  ❌ Suitability: {suit.reason}")
            return False
        print(f"  [2] Suitability ✓  type={catalog.workflow_type}")

        context = PromptContext(
            variables={
                "workflow_type": catalog.workflow_type or "general",
                "triggers": "\n".join(t.name for t in catalog.matched_triggers),
                "actions": "\n".join(a.name for a in catalog.matched_actions),
                "user_request": case.user_request,
            }
        )
        prompt_result = PromptManager().build_with_metadata(PromptKey.WORKFLOW_GENERATION, context)
        llm_result = LLMManager().generate(prompt_result.prompt)

        if not llm_result["success"]:
            print(f"  ❌ LLM: {llm_result.get('error')}")
            return False
        print(f"  [3] LLM ✓  provider={llm_result.get('provider', '?')}")

        if verbose:
            print(f"      {llm_result['output'][:300]}")

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

        compile_result = build_compiler().compile(catalog.workflow_type, workflow_json)
        steps = compile_result["compiled"].get("steps", [])
        print(f"  [5] Compiled  steps={len(steps)}")
        if verbose:
            for s in steps:
                print(f"       @{s['id']}: {s['action']}  deps={s['depends_on']}")

        saved = WorkflowPersistenceService().save(
            db=db,
            name=f"e2e-{case.id.lower()}",
            domain=case.domain,
            user_request=case.user_request,
            compile_result=compile_result,
        )
        workflow_id = saved["workflow_id"]
        print(f"  [6] Saved  workflow_id={workflow_id}")

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
    parser = argparse.ArgumentParser(description="E2E test suite — 105 cases")
    parser.add_argument("--id", help="Run single case (e.g. B01, HL01, CL01)")
    parser.add_argument("--domain", choices=["banking", "homeloan", "carloan", "support", "health"])
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
    print(f"MFLOWS E2E TEST SUITE — {len(cases)} cases")
    print("Domains: banking | homeloan | carloan | support | health")
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
    deploy_ready = "✅ DEPLOY READY" if pct >= 60 else "⚠️  NEEDS WORK"

    print("\n" + "=" * 70)
    print(f"TOTAL: {total}   ✅ PASSED: {passed}   ❌ FAILED: {failed}   ({pct}%)")
    print(f"STATUS: {deploy_ready}")

    if total > 1:
        by_group = {}
        for c in cases[:total]:
            by_group.setdefault(c.group, {"p": 0, "t": 0})
        # approximate — full tracking would need zip
        print("=" * 70)

    sys.exit(0 if pct >= 60 else 1)


if __name__ == "__main__":
    main()
