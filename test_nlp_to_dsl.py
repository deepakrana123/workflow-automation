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
