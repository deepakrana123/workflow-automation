"""
scripts/test_extractor.py

Knowledge Ingestion Evaluation Script.

Tests the full ingestion pipeline and evaluates embedding quality:
  1. Runs PDF/text extraction + LLM extraction + embedding mapping
  2. Loads already-ingested workflows from DB
  3. Compares embedding mapper predictions against ground truth
  4. Prints a detailed evaluation report showing where embeddings are correct/wrong

Modes:
  --ingest   : Run full ingestion (extract doc → save to DB → map embeddings)
  --evaluate : Load ingested workflows from DB and evaluate against ground truth
  --both     : Run ingestion then evaluate (default when --pdf/--txt given)
  --all-brds : Ingest all 4 BRDs from tests/brds/ then evaluate

Supported file types:
  --pdf   path/to/brd.pdf
  --txt   path/to/brd.txt   (plain-text BRDs, bypasses PDF extractor)

Run:
    .venv\\Scripts\\python.exe scripts/test_extractor.py --evaluate
    .venv\\Scripts\\python.exe scripts/test_extractor.py --evaluate --no-ranking
    .venv\\Scripts\\python.exe scripts/test_extractor.py --txt tests/brds/brd_01_personal_loan_origination.txt --ingest
    .venv\\Scripts\\python.exe scripts/test_extractor.py --txt tests/brds/brd_01_personal_loan_origination.txt --both
    .venv\\Scripts\\python.exe scripts/test_extractor.py --all-brds
    .venv\\Scripts\\python.exe scripts/test_extractor.py --pdf "C:\\path\\to\\brd.pdf" --both
"""

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from app.db.session import SessionLocal
from app.knowledge_ingestions.extractor import DocumentExtractor
from app.knowledge_ingestions.worfklow_extractors import WorkflowExtractor
from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from app.knowledge_ingestions.embedding_mapper import EmbeddingMapper
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workflow_action_mapping import WorkflowActionMapping
from app.models.workflow_trigger_mapping import WorkflowTriggerMapping
from app.models.action_definitions import ActionDefinition
from app.models.trigger_definitions import TriggerDefinition
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.vector_retriever import VectorRetriever
from app.retrieval.keyword_retriever import KeywordRetriever
from app.retrieval.postgress_retriever import PostgressRetriever
from app.retrieval.reciprocal_rank_fusion import ReciprocalRankFusion

from app.evaluation.evaluator import Evaluator, ExpectedWorkflow, ExtractedAction, ExtractedTrigger
from app.evaluation.report import print_report


# ── BRD file registry ─────────────────────────────────────────────────────────
# All .txt BRDs shipped in tests/brds/

_BRD_DIR = Path(__file__).parent.parent / "tests" / "brds"

ALL_BRDS: list[Path] = [
    _BRD_DIR / "brd_01_personal_loan_origination.txt",
    _BRD_DIR / "brd_02_fraud_detection_response.txt",
    _BRD_DIR / "brd_03_home_loan_origination.txt",
    _BRD_DIR / "brd_04_car_loan_workflow.txt",
]


# ── Ground Truth ──────────────────────────────────────────────────────────────
# Canonical action/trigger names come from the dispatcher ACTION_MAP.
# workflow_name must match what the LLM returns for that BRD.
#
# Trigger names come from trigger_definitions table.
# Action names come from action_definitions table (dispatcher ACTION_MAP keys).

GROUND_TRUTH: list[ExpectedWorkflow] = [

    # ── BRD-FIN-001: Personal Loan Origination ────────────────────────────────
    ExpectedWorkflow(
        workflow_name="Personal Loan Origination",
        expected_triggers=["loan_application_received"],
        expected_actions=[
            "initiate_kyc",
            "send_document_checklist",
            "verify_submitted_documents",
            "run_cibil_check",
            "send_cibil_low_alert",
            "send_rejection_letter",
            "run_income_verification",
            "calculate_risk_score",
            "approve_underwriting",
            "issue_sanction_letter",
            "send_loan_offer",
            "generate_loan_agreement",
            "generate_repayment_schedule",
            "disburse_loan",
            "send_disbursement_advice",
            "link_insurance_to_loan",
            "send_payment_reminder",
        ],
    ),

    # ── BRD-FIN-002: Fraud Detection and Response ─────────────────────────────
    ExpectedWorkflow(
        workflow_name="Fraud Detection and Response",
        expected_triggers=["fraudulent_transaction_detected"],
        expected_actions=[
            "freeze_suspicious_account",
            "hold_funds",
            "aml_screening",
            "sanctions_check",
            "send_sms_notification",
            "send_email_notification",
            "send_risk_alert",
            "flag_for_review",
            "create_audit_record",
            "submit_regulatory_report",
            "calculate_risk_score",
            "flag_high_risk_customer",
            "release_funds",
        ],
    ),

    # ── BRD-FIN-003: Home Loan Origination ───────────────────────────────────
    ExpectedWorkflow(
        workflow_name="Home Loan Origination and Disbursement",
        expected_triggers=["loan_application_received"],
        expected_actions=[
            "initiate_kyc",
            "send_document_checklist",
            "run_cibil_check",
            "send_cibil_low_alert",
            "send_rejection_letter",
            "run_income_verification",
            "initiate_property_valuation",
            "schedule_technical_visit",
            "send_technical_report",
            "initiate_legal_verification",
            "send_to_legal_team",
            "raise_legal_query",
            "legal_verification_cleared",
            "approve_underwriting",
            "issue_sanction_letter",
            "generate_loan_agreement",
            "register_mortgage",
            "collect_original_property_documents",
            "link_insurance_to_loan",
            "send_insurance_reminder",
            "disburse_tranche",
            "notify_developer_disbursement",
            "send_disbursement_advice",
            "collect_post_disbursement_documents",
        ],
    ),

    # ── BRD-FIN-004: Car Loan Origination ────────────────────────────────────
    ExpectedWorkflow(
        workflow_name="Car Loan Origination and Disbursement",
        expected_triggers=["loan_application_received"],
        expected_actions=[
            "initiate_kyc",
            "send_document_checklist",
            "run_income_verification",
            "run_cibil_check",
            "send_cibil_low_alert",
            "send_rejection_letter",
            "initiate_vehicle_valuation",
            "verify_dealer_invoice",
            "coordinate_with_dealer",
            "verify_vehicle_insurance",
            "approve_underwriting",
            "issue_sanction_letter",
            "calculate_emi",
            "generate_repayment_schedule",
            "disburse_to_dealer",
            "send_disbursement_advice",
            "send_vehicle_delivery_confirmation",
            "send_rc_endorsement_notice",
            "collect_post_disbursement_documents",
        ],
    ),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_hybrid_retriever(repo: WorkflowRepository) -> HybridRetriever:
    return HybridRetriever(
        vector_retriever=VectorRetriever(repo),
        keyword_retriever=KeywordRetriever(repo),
        postgress_retriever=PostgressRetriever(repo),
        rrf=ReciprocalRankFusion(),
    )


def _read_text_file(path: Path) -> str:
    """Read a plain-text BRD, bypassing the PDF extractor."""
    return path.read_text(encoding="utf-8")


# ── Ingestion ─────────────────────────────────────────────────────────────────

def run_ingestion(doc_path: Path) -> int:
    """
    Extract text from a PDF or .txt BRD, call LLM to extract workflow,
    save to DB, run embedding mapping.
    Returns the workflow_knowledge_id of the saved record.
    """
    print(f"\n{'=' * 60}")
    print(f"Ingesting: {doc_path.name}")
    print(f"{'=' * 60}")

    db = SessionLocal()
    try:
        workflow_extractor = WorkflowExtractor()
        repository = WorkflowRepository(db)
        hybrid = _build_hybrid_retriever(repository)
        embedding_mapper = EmbeddingMapper(repository, hybrid)

        suffix = doc_path.suffix.lower()

        if suffix == ".txt":
            print("[1] Reading plain-text BRD...")
            text = _read_text_file(doc_path)
        else:
            print("[1] Extracting text from PDF...")
            document_extractor = DocumentExtractor()
            text = document_extractor.extract(doc_path)

        print(f"    Extracted {len(text):,} characters")

        print("[2] Running LLM extraction (Gemini)...")
        workflow = workflow_extractor.extract(text)
        print(f"    Workflow name  : {workflow.workflow_name}")
        print(f"    Triggers found : {len(workflow.triggers)}")
        print(f"    Actions found  : {len(workflow.action_references)}")
        print(f"    Business rules : {len(workflow.business_rules)}")

        for t in workflow.triggers:
            print(f"      trigger: {t.name}")
        for a in workflow.action_references:
            print(f"      action : {a.name}")

        print("[3] Saving to database...")
        knowledge = repository.save(workflow)
        print(f"    Saved workflow_knowledge_id={knowledge.id}")

        print("[4] Running embedding mapping (HybridRetriever + RRF)...")
        embedding_mapper.map_actions()
        embedding_mapper.map_triggers()
        print("    Embedding mapping complete")

        return knowledge.id

    except Exception as e:
        print(f"\n❌ Ingestion failed: {type(e).__name__}: {e}")
        raise
    finally:
        db.close()


# ── Evaluation ────────────────────────────────────────────────────────────────

def load_workflow_from_db(db, workflow_knowledge_id: int):
    return db.query(WorkflowKnowledge).filter(
        WorkflowKnowledge.id == workflow_knowledge_id
    ).first()


def load_all_workflows_from_db(db):
    return db.query(WorkflowKnowledge).order_by(WorkflowKnowledge.id.desc()).all()


def build_extracted_actions(db, workflow_knowledge_id: int, hybrid: HybridRetriever | None = None) -> list[ExtractedAction]:
    mappings = (
        db.query(WorkflowActionMapping)
        .filter(WorkflowActionMapping.workflow_knowledge_id == workflow_knowledge_id)
        .all()
    )
    extracted = []
    for m in mappings:
        predicted_name = None
        if m.matched_action_definition_id is not None:
            action_def = db.query(ActionDefinition).filter(
                ActionDefinition.id == m.matched_action_definition_id
            ).first()
            if action_def:
                predicted_name = action_def.name

        # Re-run hybrid search to get full candidate ranking breakdown
        top_candidates = []
        if hybrid is not None:
            query = m.extract_name
            embedding = hybrid.embed(query)
            top_candidates = hybrid.search_actions(query=query, embedding=embedding, limit=20)

        extracted.append(ExtractedAction(
            extracted_name=m.extract_name,
            predicted_name=predicted_name,
            similarity_score=m.similarity_score,
            top_candidates=top_candidates,
        ))
    return extracted


def build_extracted_triggers(db, workflow_knowledge_id: int, hybrid: HybridRetriever | None = None) -> list[ExtractedTrigger]:
    mappings = (
        db.query(WorkflowTriggerMapping)
        .filter(WorkflowTriggerMapping.workflow_knowledge_id == workflow_knowledge_id)
        .all()
    )
    extracted = []
    for m in mappings:
        predicted_name = None
        if m.matched_trigger_definition_id is not None:
            trigger_def = db.query(TriggerDefinition).filter(
                TriggerDefinition.id == m.matched_trigger_definition_id
            ).first()
            if trigger_def:
                predicted_name = trigger_def.name

        # Re-run hybrid search to get full candidate ranking breakdown
        top_candidates = []
        if hybrid is not None:
            query = m.extracted_name
            embedding = hybrid.embed(query)
            top_candidates = hybrid.search_triggers(query=query, embedding=embedding, limit=20)

        extracted.append(ExtractedTrigger(
            extracted_name=m.extracted_name,
            predicted_name=predicted_name,
            similarity_score=m.similarity_score,
            top_candidates=top_candidates,
        ))
    return extracted


def print_detailed_mapping(
    extracted_actions: list[ExtractedAction],
    extracted_triggers: list[ExtractedTrigger],
    workflow_name: str,
) -> None:
    print(f"\n{'─' * 70}")
    print(f"  Detailed Mapping: {workflow_name}")
    print(f"{'─' * 70}")

    if extracted_triggers:
        print("\n  TRIGGERS")
        print(f"  {'Extracted':<35} {'Predicted':<30} {'Score':<8}")
        print(f"  {'─'*34} {'─'*29} {'─'*7}")
        for t in extracted_triggers:
            predicted = t.predicted_name or "NOT MATCHED"
            score = f"{t.similarity_score:.4f}" if t.similarity_score is not None else "  n/a "
            print(f"  {t.extracted_name:<35} {predicted:<30} {score}")

    if extracted_actions:
        print("\n  ACTIONS")
        print(f"  {'Extracted':<35} {'Predicted':<30} {'Score':<8}")
        print(f"  {'─'*34} {'─'*29} {'─'*7}")
        for a in extracted_actions:
            predicted = a.predicted_name or "NOT MATCHED"
            score = f"{a.similarity_score:.4f}" if a.similarity_score is not None else "  n/a "
            print(f"  {a.extracted_name:<35} {predicted:<30} {score}")


def run_evaluation(workflow_knowledge_ids: list[int] | None = None, with_ranking: bool = True) -> None:
    """
    Load ingested workflows from DB and evaluate embedding quality.

    If workflow_knowledge_ids is provided, evaluates only those.
    Otherwise evaluates all workflows in DB.

    If GROUND_TRUTH is empty, shows mapping tables only (no accuracy metrics).

    with_ranking: re-run hybrid search to populate per-candidate ranking breakdown.
    """
    db = SessionLocal()
    try:
        # Build retriever once for re-ranking (shared across all workflows)
        repository = WorkflowRepository(db)
        hybrid = _build_hybrid_retriever(repository) if with_ranking else None

        if workflow_knowledge_ids:
            workflows = [load_workflow_from_db(db, wid) for wid in workflow_knowledge_ids]
            workflows = [w for w in workflows if w is not None]
        else:
            workflows = load_all_workflows_from_db(db)

        if not workflows:
            print("\n⚠️  No workflows found in DB. Run ingestion first.")
            return

        print(f"\n{'=' * 70}")
        print(f"  Evaluation — {len(workflows)} workflow(s) found in DB")
        if with_ranking:
            print(f"  Ranking mode  : ON  (re-running hybrid search for top-N breakdown)")
        print(f"{'=' * 70}")

        # Only run accuracy metrics if ground truth is defined
        if not GROUND_TRUTH:
            # Fallback: show mapping tables without accuracy
            for wf in workflows:
                extracted_actions = build_extracted_actions(db, wf.id)
                extracted_triggers = build_extracted_triggers(db, wf.id)
                print_detailed_mapping(extracted_actions, extracted_triggers, wf.workflow_name)
            print("\n\nℹ️  GROUND_TRUTH is empty — mapping tables shown above.")
            print("   Add ExpectedWorkflow entries to GROUND_TRUTH to see accuracy metrics.")
            return

        evaluator = Evaluator()
        gt_by_name = {g.workflow_name: g for g in GROUND_TRUTH}
        workflow_evaluations = []

        for wf in workflows:
            expected = gt_by_name.get(wf.workflow_name)
            if expected is None:
                print(f"\n⚠️  No ground truth for '{wf.workflow_name}' — skipping accuracy")
                continue

            print(f"  Evaluating: {wf.workflow_name}  (id={wf.id})")
            extracted_actions = build_extracted_actions(db, wf.id, hybrid=hybrid)
            extracted_triggers = build_extracted_triggers(db, wf.id, hybrid=hybrid)

            wf_eval = evaluator.evaluate_workflow(
                workflow_name=wf.workflow_name,
                extracted_actions=extracted_actions,
                extracted_triggers=extracted_triggers,
                expected=expected,
            )
            workflow_evaluations.append(wf_eval)

        if workflow_evaluations:
            report = evaluator.build_report(workflow_evaluations)
            print("\n")
            print_report(report)

    finally:
        db.close()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="MFlows Knowledge Ingestion Evaluation"
    )

    # Input source (mutually exclusive)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--pdf", type=str, default=None, help="Path to BRD PDF file")
    source.add_argument("--txt", type=str, default=None, help="Path to plain-text BRD file")
    source.add_argument(
        "--all-brds",
        action="store_true",
        help=f"Ingest all {len(ALL_BRDS)} BRDs from tests/brds/ then evaluate",
    )

    # Modes
    parser.add_argument("--ingest",   action="store_true", help="Run ingestion pipeline")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate from DB")
    parser.add_argument("--both",     action="store_true", help="Ingest then evaluate")
    parser.add_argument(
        "--no-ranking",
        action="store_true",
        help="Skip re-running hybrid search for ranking breakdown (faster, less detail)",
    )
    parser.add_argument(
        "--workflow-id",
        type=int,
        default=None,
        help="Evaluate a specific workflow_knowledge_id from DB",
    )
    args = parser.parse_args()

    # ── --all-brds: ingest all BRDs then evaluate ─────────────────────────────
    if args.all_brds:
        missing = [p for p in ALL_BRDS if not p.exists()]
        if missing:
            for p in missing:
                print(f"❌ BRD file not found: {p}")
            sys.exit(1)

        ingested_ids = []
        for brd_path in ALL_BRDS:
            wid = run_ingestion(brd_path)
            ingested_ids.append(wid)

        run_evaluation(workflow_knowledge_ids=ingested_ids, with_ranking=not args.no_ranking)
        return

    # ── Single-file modes ─────────────────────────────────────────────────────
    doc_path: Path | None = None
    if args.pdf:
        doc_path = Path(args.pdf)
    elif args.txt:
        doc_path = Path(args.txt)

    # Default: if a file was given with no mode flag → --both
    if doc_path and not args.ingest and not args.evaluate and not args.both:
        args.both = True

    # Default: if no file and no mode → evaluate only
    if not doc_path and not args.ingest and not args.evaluate and not args.both:
        args.evaluate = True

    ingested_id = None

    if args.ingest or args.both:
        if not doc_path:
            print("❌ Provide --pdf or --txt for ingestion")
            sys.exit(1)
        if not doc_path.exists():
            print(f"❌ File not found: {doc_path}")
            sys.exit(1)
        ingested_id = run_ingestion(doc_path)

    if args.evaluate or args.both:
        ids = None
        if args.workflow_id:
            ids = [args.workflow_id]
        elif ingested_id:
            ids = [ingested_id]
        run_evaluation(workflow_knowledge_ids=ids, with_ranking=not args.no_ranking)


if __name__ == "__main__":
    main()
