"""
scripts/test_semantic_e2e.py

Full end-to-end test using SEMANTIC inputs only.
All queries use synonyms/paraphrases — keyword matching would fail these.
Pipeline: semantic search → catalog → LLM → compile → save → execute → COMPLETED

Requirements:
    docker-compose up   (all services including worker)
    backfill_embeddings must have been run

Run:
    .venv\\Scripts\\python.exe scripts/test_semantic_e2e.py
    .venv\\Scripts\\python.exe scripts/test_semantic_e2e.py --id S01
    .venv\\Scripts\\python.exe scripts/test_semantic_e2e.py --domain finance
    .venv\\Scripts\\python.exe scripts/test_semantic_e2e.py --stop-on-fail
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
class SemanticE2ECase:
    id: str
    domain: str
    description: str
    user_request: str   # uses synonyms — keyword match would miss this


CASES = [
    # ── Finance (5 cases) ─────────────────────────────────────────────────────
    SemanticE2ECase(
        "S01", "finance",
        "invoice unpaid → alert supervisor + freeze account",
        "invoice still unpaid alert supervisor and freeze the account",
    ),
    SemanticE2ECase(
        "S02", "finance",
        "suspicious activity → mark for investigation + log compliance record",
        "suspicious account activity mark for investigation and log compliance record",
    ),
    SemanticE2ECase(
        "S03", "finance",
        "bill past due → remind customer then escalate to higher authority",
        "bill is past due remind customer then escalate to higher authority",
    ),
    SemanticE2ECase(
        "S04", "finance",
        "fraudulent transaction → freeze account then create audit trail then alert supervisor",
        "fraudulent transaction detected freeze the account then create audit trail then alert supervisor",
    ),
    SemanticE2ECase(
        "S05", "finance",
        "account suspended → restore access + notify manager",
        "user account suspended restore account access and tell the manager",
    ),

    # ── Support (5 cases) ─────────────────────────────────────────────────────
    SemanticE2ECase(
        "S06", "support",
        "new issue opened → route to agent then inform customer",
        "new issue was opened route ticket to an agent then inform customer about update",
    ),
    SemanticE2ECase(
        "S07", "support",
        "response time exceeded → push to tier two + alert supervisor",
        "response time exceeded push to tier two team and alert supervisor about this",
    ),
    SemanticE2ECase(
        "S08", "support",
        "customer cancelled subscription → send satisfaction form + notify manager",
        "customer cancelled subscription send customer satisfaction form and tell the manager",
    ),
    SemanticE2ECase(
        "S09", "support",
        "customer wants money back → initiate money return then mark ticket as done",
        "customer wants money back initiate money return then mark ticket as done",
    ),
    SemanticE2ECase(
        "S10", "support",
        "complaint filed → assign employee then fix the issue then send update",
        "complaint filed by customer assign employee to ticket then fix the support issue then inform customer about update",
    ),

    # ── Health (5 cases) ──────────────────────────────────────────────────────
    SemanticE2ECase(
        "S11", "health",
        "patient checked into hospital → book appointment + notify manager",
        "patient checked into hospital book appointment for patient and notify manager",
    ),
    SemanticE2ECase(
        "S12", "health",
        "vital signs critical → alert medical team then refer to specialist",
        "vital signs critical alert the medical team then refer patient to specialist",
    ),
    SemanticE2ECase(
        "S13", "health",
        "prescription overdue → send pill reminder then check in on wellness",
        "prescription overdue send pill reminder to patient then check in on patient wellness",
    ),
    SemanticE2ECase(
        "S14", "health",
        "patient left hospital → send home care instructions + log compliance record",
        "patient left the hospital send home care instructions and log compliance record",
    ),
    SemanticE2ECase(
        "S15", "health",
        "patient condition deteriorated → activate emergency response then notify medical team",
        "patient condition deteriorated activate emergency response then notify care staff immediately",
    ),

    # ── Mixed hard cases (5 cases) ────────────────────────────────────────────
    SemanticE2ECase(
        "S16", "finance",
        "emi overdue → warn customer then raise case + log compliance",
        "emi is overdue send payment warning to customer then raise the case to higher level and log compliance record",
    ),
    SemanticE2ECase(
        "S17", "support",
        "grievance raised → route to agent + move to second level + send satisfaction form",
        "customer raised a grievance route ticket to an agent then move to second level support then send customer satisfaction form",
    ),
    SemanticE2ECase(
        "S18", "health",
        "test results available → notify about result then book follow up",
        "test results are available notify about test result then book appointment for patient",
    ),
    SemanticE2ECase(
        "S19", "finance",
        "credit request → tag as suspicious + alert supervisor + log audit",
        "credit request received tag as suspicious and alert supervisor about this then create audit trail",
    ),
    SemanticE2ECase(
        "S20", "support",
        "ticket not closed → move to tier2 + inform customer + mark done",
        "issue still pending move to second level support and inform customer about update then mark ticket as done",
    ),
]


def build_compiler():
    return WorkflowCompilerService(
        dsl_generator=DSLGenerator(),
        rule_parser=RuleParser(),
        ast_builder=WorkflowASTBuilder(),
        ast_validator=ASTValidator(),
        workflow_compiler=WorkflowComplier(),
    )


def run_case(case: SemanticE2ECase, verbose: bool) -> bool:
    print(f"\n{'─' * 70}")
    print(f"  [{case.id}] {case.description}")
    print(f"  Input : \"{case.user_request}\"")
    print(f"  Domain: {case.domain}")
    print(f"{'─' * 70}")

    db = SessionLocal()
    try:
        # 1 — Semantic catalog match
        matcher = CatalogMatcher(
            trigger_repository=TriggerDefinitionRepository(db),
            action_repository=ActionDefinitionRepository(db),
            semantic_retriever=SemanticCatalogRetriever(),
        )
        catalog = matcher.match(db, case.user_request)

        print(f"  [1] Catalog  triggers={catalog.trigger_names}  actions={catalog.action_names}")

        # 2 — Suitability
        suit = SuitabilityAgent().evaluate(
            catalog.workflow_type,
            catalog.trigger_names,
            catalog.action_names,
        )
        if not suit.supported:
            print(f"  ❌ Suitability rejected: {suit.reason}")
            return False
        print(f"  [2] Suitability ✓  workflow_type={catalog.workflow_type}")

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
        print(f"  [3] LLM OK  provider={llm_result.get('provider', 'unknown')}")

        # 4 — Parse + validate
        workflow_json = WorkflowResponseParser().parse(llm_result["output"])
        schema_r = WorkflowSchemaValidator().validate(workflow_json)
        if not schema_r.valid:
            print(f"  ❌ Schema invalid: {schema_r.errors}")
            return False

        wf_r = WorkflowValidator().validate(workflow_json)
        if not wf_r.valid:
            print(f"  ❌ Workflow invalid: {wf_r.errors}")
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
            name=f"sem-e2e-{case.id.lower()}",
            domain=case.domain,
            user_request=case.user_request,
            compile_result=compile_result,
        )
        workflow_id = saved["workflow_id"]
        print(f"  [6] Saved  workflow_id={workflow_id}")

        # 7 — Execute
        resp = requests.post(
            f"{BASE_URL}/api/execute/",
            json={"workflow_id": workflow_id, "entity_id": f"sem-{case.id.lower()}"},
            timeout=10,
        )
        resp.raise_for_status()
        body = resp.json()
        if not body.get("success"):
            print(f"  ❌ Execute failed: {body}")
            return False

        execution_id = body["workflow_execution_id"]
        print(f"  [7] Queued  execution_id={execution_id}  polling", end="", flush=True)

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
            print(f"  ❌ FAILED — final status: {final_status}")
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
    parser = argparse.ArgumentParser(description="Semantic E2E test")
    parser.add_argument("--id", help="Run single case (e.g. S01)")
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
        cases = [c for c in CASES if c.domain == args.domain]

    print("\n" + "=" * 70)
    print(f"SEMANTIC E2E TEST — {len(cases)} cases")
    print("All inputs use synonyms (keyword match would fail these)")
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
    print("\n" + "=" * 70)
    print(f"TOTAL: {total}   ✅ PASSED: {passed}   ❌ FAILED: {failed}   ({pct}%)")
    print("=" * 70)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
