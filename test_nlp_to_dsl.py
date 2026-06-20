"""
test_nlp_to_dsl.py

Real end-to-end NLP → DSL pipeline test.
Uses the real DB catalog (CatalogMatcher pulls triggers/actions from DB).

Flow:
  User text
    → CatalogMatcher (DB lookup)
    → SuitabilityAgent
    → PromptBuilder
    → LLMManager (real LLM call)
    → WorkflowResponseParser
    → SchemaValidator + WorkflowValidator
    → DSLGenerator (@step format)
    → RuleParser → ASTBuilder → ASTValidator → WorkflowCompiler
    → print compiled output

Requirements:
    docker-compose up api redis   (needs DB connection)

Run:
    .venv\\Scripts\\python.exe test_nlp_to_dsl.py
"""

import sys
import traceback
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
from app.dsl.dsl_generator import DSLGenerator
from app.nlp.parsers.rule_parser import RuleParser
from app.nlp.ast.builder import WorkflowASTBuilder
from app.nlp.ast.validator import ASTValidator
from app.nlp.complier.workflow_complier import WorkflowComplier


CASES = [
    # ── Finance ───────────────────────────────────────────────────────────────
    ("A01", "When payment is missed escalate case and notify manager then create audit record"),
    ("A02", "When payment is missed escalate case and notify manager"),
    ("A03", "When payment is due send reminder then escalate case then notify manager"),
    ("A04", "if fraud detected lock account then flag for review then notify manager"),
    ("A05", "When ticket created assign support agent then notify customer and notify manager then close case"),
    ("F01", "When fraud is detected lock account and create audit record then notify manager"),
    ("F02", "When payment is due send reminder then escalate case"),
    ("F03", "When account is locked notify manager and create audit record"),

    # ── Support ───────────────────────────────────────────────────────────────
    ("S01", "When ticket is created assign support agent then send customer update then resolve ticket"),
    ("S02", "When SLA is breached send sla breach alert then escalate to tier2 then notify manager"),
    ("S03", "When complaint is created create support ticket and notify manager then escalate case"),
    ("S04", "When refund is requested process refund then send customer update"),
    ("S05", "When customer churned send satisfaction survey and notify manager"),

    # ── Health ────────────────────────────────────────────────────────────────
    ("H01", "When patient is admitted schedule appointment and notify manager"),
    ("H02", "When critical vitals detected alert care team then escalate to specialist then notify manager"),
    ("H03", "When medication is overdue send medication reminder then notify manager"),
    ("H04", "When lab result is ready notify lab result and alert care team"),
    ("H05", "When patient is discharged send discharge instructions and create audit record"),

    # ── Boundary — phrasing variants ──────────────────────────────────────────
    ("B01", "payment is due send reminder"),                                          # no when keyword
    ("B02", "WHEN PAYMENT IS DUE SEND REMINDER THEN ESCALATE CASE"),                 # all caps
    ("B03", "When   payment   is   due   send   reminder"),                           # extra whitespace
    ("B04", "When payment due remind and notify"),                                    # terse minimal
    ("B05", "When fraud detected lock account then flag for review then audit it"),   # unknown action at end

    # ── Boundary — multi-action chains ────────────────────────────────────────
    ("C01", "When payment is missed send reminder then escalate case then notify manager then create audit record"),  # 4-step chain
    ("C02", "When ticket created assign support agent then send customer update and notify manager then resolve ticket then close case"),  # 5-step mixed
    ("C03", "When fraud detected lock account and flag for review then notify manager and create audit record"),      # two parallel pairs

    # ── Boundary — domain crossing ────────────────────────────────────────────
    ("D01", "When critical vitals detected alert care team and notify manager and escalate to specialist"),  # 3-way parallel health
    ("D02", "When complaint created create support ticket and notify manager"),                               # support parallel
    ("D03", "When account locked notify manager then create audit record then generate report"),              # finance 3-step

    # ── Edge — LLM stress ─────────────────────────────────────────────────────
    ("E01", "When payment is due send reminder"),                                     # single action minimal
    ("E02", "When ticket created assign support agent"),                              # single action support
    ("E03", "When patient discharged send discharge instructions"),                   # single action health

   ("P01", "When payment is missed notify manager and create audit record"),
("P02", "When fraud detected lock account and notify manager"),
("P03", "When ticket created notify customer and notify manager"),
("P04", "When patient admitted notify manager and alert care team"),
("P05", "When critical vitals detected alert care team and escalate to specialist"),

("D10", "When payment missed escalate case and notify manager then create audit record"),
("D11", "When fraud detected lock account and flag for review then notify manager"),
("D12", "When ticket created assign support agent then notify customer and notify manager then close case"),
("D13", "When patient admitted schedule appointment and notify manager then create audit record"),
("D14", "When complaint created create support ticket and notify manager then escalate case"),

("L01", "When payment due send reminder then escalate case then notify manager then create audit record"),
("L02", "When fraud detected lock account then flag for review then notify manager then create audit record"),
("L03", "When ticket created assign support agent then send customer update then resolve ticket then close case"),
("L04", "When patient admitted schedule appointment then notify manager then create audit record"),
("L05", "When medication overdue send medication reminder then notify manager then create audit record"),

("M01", "When payment missed send reminder and notify manager then escalate case"),
("M02", "When fraud detected lock account and flag for review then create audit record"),
("M03", "When ticket created notify customer and notify manager then resolve ticket"),
("M04", "When patient discharged send discharge instructions and notify manager then create audit record"),
("M05", "When critical vitals detected alert care team and escalate to specialist then notify manager"),

("N01", "payment due remind customer"),
("N02", "payment missed escalate"),
("N03", "fraud detected lock immediately"),
("N04", "new ticket assign agent"),
("N05", "patient admitted book appointment"),

("X01", "handle payment"),
("X02", "process ticket"),
("X03", "manage fraud"),
("X04", "help patient"),
("X05", "send notification"),

("U01", "When payment due send sms"),
("U02", "When ticket created send whatsapp message"),
("U03", "When patient admitted call doctor"),
("U04", "When fraud detected freeze card permanently"),
("U05", "When complaint created send email blast"),

("T01", "When payment due send reminder then escalate case then notify manager then create audit record then notify customer"),
("T02", "When ticket created assign support agent then notify customer then notify manager then resolve ticket then close case"),
("T03", "When fraud detected lock account then flag for review then notify manager then create audit record then generate report"),
("T04", "When patient admitted schedule appointment then alert care team then notify manager then create audit record"),
("T05", "When critical vitals detected alert care team then escalate to specialist then notify manager then create audit record"),


]

# shared instances
suitability  = SuitabilityAgent()
prompt_builder   = PromptBuilder()
llm_manager      = LLMManager()
response_parser  = WorkflowResponseParser()
schema_validator = WorkflowSchemaValidator()
wf_validator     = WorkflowValidator()
dsl_gen          = DSLGenerator()
rule_parser      = RuleParser()
ast_builder      = WorkflowASTBuilder()
ast_validator    = ASTValidator()
compiler         = WorkflowComplier()


def run_case(case_id: str, user_request: str) -> bool:
    print(f"\n{'─' * 65}")
    print(f"  [{case_id}] \"{user_request}\"")
    print(f"{'─' * 65}")

    db = SessionLocal()
    try:
        # 1 — Catalog lookup from DB
        catalog = CatalogMatcher(
            TriggerDefinitionRepository(db),
            ActionDefinitionRepository(db),
        ).match(user_request)

        print(f"\n  [1] Catalog matched")
        print(f"      workflow_type : {catalog.workflow_type}")
        print(f"      triggers      : {catalog.trigger_names}")
        print(f"      actions       : {catalog.action_names}")

        # 2 — Suitability check
        suit = suitability.evaluate(catalog.workflow_type, catalog.trigger_names, catalog.action_names)
        if not suit.supported:
            print(f"\n  ❌ Suitability rejected: {suit.reason}")
            return False
        print(f"  [2] Suitability ✓")

        # 3 — Build prompt
        context = PromptContext(
            workflow_type=catalog.workflow_type,
            triggers=[t.name for t in catalog.matched_triggers],
            actions=[a.name for a in catalog.matched_actions],
            user_request=user_request,
        )
        build_result = prompt_builder.build(context)
        print(f"  [3] Prompt built  version={build_result.version}  ~{build_result.estimated_tokens} tokens")

        # 4 — LLM call
        llm_result = llm_manager.generate(build_result.prompt)
        if not llm_result["success"]:
            print(f"\n  ❌ LLM failed: {llm_result.get('error')}")
            return False
        print(f"  [4] LLM responded")
        print(f"      {llm_result['output'][:300]}")

        # 5 — Parse JSON
        workflow = response_parser.parse(llm_result["output"])
        print(f"\n  [5] JSON parsed:")
        for t in workflow["workflow"]["triggers"]:
            print(f"      trigger: {t['name']}")
        for a in workflow["workflow"]["actions"]:
            print(f"      action : {a['name']}  deps={a.get('dependencies', [])}")

        # 6 — Validate
        schema_r = schema_validator.validate(workflow)
        if not schema_r.valid:
            print(f"\n  ❌ Schema invalid: {schema_r.errors}")
            return False

        wf_r = wf_validator.validate(workflow)
        if not wf_r.valid:
            print(f"\n  ❌ Workflow invalid: {wf_r.errors}")
            return False
        print(f"  [6] Validation ✓")

        # 7 — Generate DSL
        dsl = dsl_gen.generate(catalog.workflow_type, workflow)
        print(f"\n  [7] DSL:")
        for line in dsl.splitlines():
            print(f"      {line}")

        # 8 — Parse DSL → nodes → AST → compile
        nodes = rule_parser.parse(dsl)
        if not nodes:
            print(f"\n  ❌ RuleParser returned no nodes")
            return False

        ast = ast_builder.build(nodes)
        ast_validator.validate(ast)

        compiled = compiler.compile(ast)
        print(f"\n  [8] Compiled:")
        print(f"      trigger: {compiled['trigger']}")
        for step in compiled["steps"]:
            print(f"      step {step['id']}: {step['action']}  depends_on={step['depends_on']}")

        print(f"\n  ✅ PASSED")
        return True

    except Exception as e:
        print(f"\n  ❌ FAILED — {type(e).__name__}: {e}")
        print(f"  {traceback.format_exc()}")
        return False
    finally:
        db.close()


def main():
    print("\n" + "=" * 65)
    print("NLP → DSL PIPELINE TEST  (real DB + real LLM)")
    print("=" * 65)

    results = [run_case(cid, req) for cid, req in CASES]

    passed = sum(results)
    failed = len(results) - passed

    print("\n" + "=" * 65)
    print(f"TOTAL: {len(results)}   ✅ PASSED: {passed}   ❌ FAILED: {failed}")
    print("=" * 65)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
