"""
scripts/test_extractor.py

Knowledge Ingestion Evaluation Script.

Tests the full ingestion pipeline and evaluates embedding quality:
  1. Runs PDF extraction + LLM extraction + embedding mapping (optional)
  2. Loads already-ingested workflows from DB
  3. Compares embedding mapper predictions against ground truth
  4. Prints a detailed evaluation report showing where embeddings are correct/wrong

Modes:
  --ingest   : Run full ingestion (extract PDF → save to DB → map embeddings)
  --evaluate : Load ingested workflows from DB and evaluate against ground truth
  --both     : Run ingestion then evaluate (default)

Ground truth is defined inline in GROUND_TRUTH below.
Add one entry per workflow you have ingested. Use canonical catalog names.

Run:
    .venv\\Scripts\\python.exe scripts/test_extractor.py --evaluate
    .venv\\Scripts\\python.exe scripts/test_extractor.py --ingest --pdf "C:\\path\\to\\brd.pdf"
    .venv\\Scripts\\python.exe scripts/test_extractor.py --both   --pdf "C:\\path\\to\\brd.pdf"
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

from app.evaluation.evaluator import Evaluator, ExpectedWorkflow, ExtractedAction, ExtractedTrigger
from app.evaluation.report import print_report


# ── Ground Truth ──────────────────────────────────────────────────────────────
# Define expected canonical action/trigger names per workflow.
# workflow_name must match the name extracted by the LLM from the BRD.
# Use exact names from action_definitions and trigger_definitions tables.
#
# Example:
#   ExpectedWorkflow(
#       workflow_name="Home Loan Origination",
#       expected_actions=["run_cibil_check", "initiate_property_valuation", "send_to_legal_team"],
#       expected_triggers=["loan_application_received"],
#   ),

GROUND_TRUTH: list[ExpectedWorkflow] = [
    # Add your ground truth entries here.
    # One entry per workflow ingested from BRD.
    #
    # ExpectedWorkflow(
    #     workflow_name="<workflow name as extracted by LLM>",
    #     expected_actions=["canonical_action_1", "canonical_action_2"],
    #     expected_triggers=["canonical_trigger_1"],
    # ),
]


# ── Ingestion ─────────────────────────────────────────────────────────────────

def run_ingestion(pdf_path: Path) -> int:
    """
    Extract text from PDF, call LLM to extract workflow, save to DB, run embedding mapping.
    Returns the workflow_knowledge_id of the saved record.
    """
    print(f"\n{'=' * 60}")
    print(f"Ingesting: {pdf_path.name}")
    print(f"{'=' * 60}")

    db = SessionLocal()
    try:
        document_extractor = DocumentExtractor()
        workflow_extractor = WorkflowExtractor()
        repository = WorkflowRepository(db)
        embedding_mapper = EmbeddingMapper(repository)

        print("[1] Extracting text from PDF...")
        text = document_extractor.extract(pdf_path)
        print(f"    Extracted {len(text)} characters")

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

        print("[4] Running embedding mapping...")
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
    """Load a WorkflowKnowledge record with its action and trigger mappings."""
    return db.query(WorkflowKnowledge).filter(
        WorkflowKnowledge.id == workflow_knowledge_id
    ).first()


def load_all_workflows_from_db(db):
    """Load all WorkflowKnowledge records ordered by most recent first."""
    return db.query(WorkflowKnowledge).order_by(WorkflowKnowledge.id.desc()).all()


def build_extracted_actions(db, workflow_knowledge_id: int) -> list[ExtractedAction]:
    """
    Build ExtractedAction list from WorkflowActionMapping rows.
    Joins to ActionDefinition to get the predicted canonical name.
    """
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

        extracted.append(ExtractedAction(
            extracted_name=m.extract_name,
            predicted_name=predicted_name,
            similarity_score=m.similarity_score,
        ))

    return extracted


def build_extracted_triggers(db, workflow_knowledge_id: int) -> list[ExtractedTrigger]:
    """
    Build ExtractedTrigger list from WorkflowTriggerMapping rows.
    Joins to TriggerDefinition to get the predicted canonical name.
    """
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

        extracted.append(ExtractedTrigger(
            extracted_name=m.extracted_name,
            predicted_name=predicted_name,
            similarity_score=m.similarity_score,
        ))

    return extracted


def print_detailed_mapping(
    extracted_actions: list[ExtractedAction],
    extracted_triggers: list[ExtractedTrigger],
    workflow_name: str,
) -> None:
    """Print a detailed per-item mapping table — useful for debugging embeddings."""
    print(f"\n{'─' * 60}")
    print(f"  Detailed Mapping: {workflow_name}")
    print(f"{'─' * 60}")

    if extracted_triggers:
        print("\n  TRIGGERS")
        print(f"  {'Extracted':<35} {'Predicted':<35} {'Score':<8}")
        print(f"  {'─'*34} {'─'*34} {'─'*7}")
        for t in extracted_triggers:
            predicted = t.predicted_name or "NOT MATCHED"
            score = f"{t.similarity_score:.3f}" if t.similarity_score is not None else "  n/a "
            print(f"  {t.extracted_name:<35} {predicted:<35} {score}")

    if extracted_actions:
        print("\n  ACTIONS")
        print(f"  {'Extracted':<35} {'Predicted':<35} {'Score':<8}")
        print(f"  {'─'*34} {'─'*34} {'─'*7}")
        for a in extracted_actions:
            predicted = a.predicted_name or "NOT MATCHED"
            score = f"{a.similarity_score:.3f}" if a.similarity_score is not None else "  n/a "
            print(f"  {a.extracted_name:<35} {predicted:<35} {score}")


def run_evaluation(workflow_knowledge_ids: list[int] | None = None) -> None:
    """
    Load ingested workflows from DB and evaluate embedding quality.

    If workflow_knowledge_ids is provided, evaluates only those workflows.
    Otherwise evaluates all workflows in DB.

    If GROUND_TRUTH is empty, skips accuracy metrics and shows mapping tables only.
    """
    db = SessionLocal()
    try:
        if workflow_knowledge_ids:
            workflows = [load_workflow_from_db(db, wid) for wid in workflow_knowledge_ids]
            workflows = [w for w in workflows if w is not None]
        else:
            workflows = load_all_workflows_from_db(db)

        if not workflows:
            print("\n⚠️  No workflows found in DB. Run ingestion first.")
            return

        print(f"\n{'=' * 60}")
        print(f"Found {len(workflows)} workflow(s) in DB")
        print(f"{'=' * 60}")

        # Always show detailed mapping tables
        for wf in workflows:
            extracted_actions = build_extracted_actions(db, wf.id)
            extracted_triggers = build_extracted_triggers(db, wf.id)
            print_detailed_mapping(extracted_actions, extracted_triggers, wf.workflow_name)

        # Only run accuracy evaluation if ground truth is defined
        if not GROUND_TRUTH:
            print("\n\nℹ️  GROUND_TRUTH is empty — showing mapping tables only.")
            print("   Add ExpectedWorkflow entries to GROUND_TRUTH in this script")
            print("   to see accuracy metrics (action_accuracy, trigger_accuracy, avg_similarity).")
            return

        # Match ground truth to DB workflows by name
        evaluator = Evaluator()
        gt_by_name = {g.workflow_name: g for g in GROUND_TRUTH}
        workflow_evaluations = []

        for wf in workflows:
            expected = gt_by_name.get(wf.workflow_name)
            if expected is None:
                print(f"\n⚠️  No ground truth for workflow: '{wf.workflow_name}' — skipping accuracy")
                continue

            extracted_actions = build_extracted_actions(db, wf.id)
            extracted_triggers = build_extracted_triggers(db, wf.id)

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
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Run ingestion pipeline (requires --pdf)",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Evaluate embedding quality from DB",
    )
    parser.add_argument(
        "--both",
        action="store_true",
        help="Run ingestion then evaluate",
    )
    parser.add_argument(
        "--pdf",
        type=str,
        default=None,
        help="Path to BRD PDF file (required for --ingest and --both)",
    )
    parser.add_argument(
        "--workflow-id",
        type=int,
        default=None,
        help="Evaluate a specific workflow_knowledge_id from DB",
    )
    args = parser.parse_args()

    # Default: evaluate only
    if not args.ingest and not args.evaluate and not args.both:
        args.evaluate = True

    ingested_id = None

    if args.ingest or args.both:
        if not args.pdf:
            print("❌ --pdf is required for ingestion")
            sys.exit(1)
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"❌ File not found: {pdf_path}")
            sys.exit(1)
        ingested_id = run_ingestion(pdf_path)

    if args.evaluate or args.both:
        ids = None
        if args.workflow_id:
            ids = [args.workflow_id]
        elif ingested_id:
            ids = [ingested_id]
        run_evaluation(workflow_knowledge_ids=ids)


if __name__ == "__main__":
    main()
