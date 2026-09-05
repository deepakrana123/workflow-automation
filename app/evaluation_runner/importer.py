"""
app/evaluation_runner/importer.py

Import ground-truth evaluation cases from a CSV or the built-in seed dataset.

CSV format (headers required):
  brd_action, description, expected_action_name, source_brd

expected_action_definition_id is resolved at import time by looking up
expected_action_name in action_definitions.name.
If not found → expected_action_definition_id = NULL (CATALOG_MISSING).
"""

from __future__ import annotations
import csv
from io import StringIO

from sqlalchemy.orm import Session

from app.models.evaluation_case import EvaluationCase
from app.models.action_definitions import ActionDefinition


# ── Built-in seed dataset ─────────────────────────────────────────────────────
# brd_action, description, expected_action_name, source_brd
# expected_action_name is the canonical ActionDefinition.name — must match exactly.
# Leave expected_action_name blank if not yet verified against the catalog.
_SEED_CSV = """\
brd_action,description,expected_action_name,source_brd
Verify Identification Credentials,Verify the applicant's government-issued identity document,,BRD-seed
Apply Interest Rate,Apply the applicable interest rate to the loan account,apply_interest,BRD-seed
Upload Documentation,Upload required supporting documents,,BRD-seed
Initiate Loan Application,Start a new loan application for the customer,approve_loan,BRD-seed
Collect Borrower Information,Gather personal and financial details from the borrower,collect_documents,BRD-seed
Manage Condition Clearance,Clear pre-disbursement conditions on the loan,,BRD-seed
Capture Fixed Deposit Details,Record the details of a fixed deposit placement,,BRD-seed
Cross-Reference Internal Records,Cross-check against existing customer records,,BRD-seed
Activate Account Ledger,Activate the customer account ledger,open_account,BRD-seed
Verify Source Account Funds,Confirm sufficient balance in the source account,hold_funds,BRD-seed
Place Debit Block,Place a debit block on the account,freeze_suspicious_account,BRD-seed
Transfer Principal Funds,Transfer loan principal to the borrower's account,disburse_loan,BRD-seed
Query Treasury Interest Matrix,Retrieve the applicable treasury interest matrix,,BRD-seed
Book Fixed Deposit Contract,Book and record the fixed deposit contract,,BRD-seed
Receive First Notice of Loss,Record the first notice of loss for an insurance claim,,BRD-seed
Verify Policy Coverage,Verify that the policy covers the claimed event,,BRD-seed
Determine Claim Type,Classify the type of insurance claim,,BRD-seed
Apply Deductible,Apply the applicable deductible to the claim,,BRD-seed
Schedule Inspection,Schedule a physical inspection of the claim,,BRD-seed
Perform Damage Assessment,Assess and document the extent of damage,,BRD-seed
Coordinate Closing,Coordinate the loan or transaction closing process,,BRD-seed
Conduct Closing,Execute the final closing of the transaction,,BRD-seed
Fund Loan,Disburse loan funds to the borrower,disburse_loan,BRD-seed
Close Loan File,Close and archive the completed loan file,close_account,BRD-seed
"""


def _resolve_action_id(db: Session, action_name: str) -> int | None:
    if not action_name or not action_name.strip():
        return None
    row = (
        db.query(ActionDefinition)
        .filter(ActionDefinition.name == action_name.strip())
        .first()
    )
    return row.id if row else None


def import_cases(
    db: Session,
    csv_text: str | None = None,
    skip_existing: bool = True,
) -> dict[str, int]:
    """
    Import evaluation cases from CSV text.

    csv_text=None uses the built-in seed dataset.
    Returns {"imported": N, "skipped": M, "catalog_missing": K}
    """
    source = csv_text or _SEED_CSV
    reader = csv.DictReader(StringIO(source))

    existing_actions = {
        c.brd_action for c in db.query(EvaluationCase.brd_action).all()
    }

    imported = skipped = catalog_missing = 0

    for row in reader:
        brd_action = row.get("brd_action", "").strip()
        if not brd_action:
            continue

        if skip_existing and brd_action in existing_actions:
            skipped += 1
            continue

        expected_name = row.get("expected_action_name", "").strip()
        expected_id   = _resolve_action_id(db, expected_name) if expected_name else None

        if expected_name and expected_id is None:
            catalog_missing += 1

        case = EvaluationCase(
            brd_action=brd_action,
            description=row.get("description", "").strip() or None,
            expected_action_definition_id=expected_id,
            expected_action_name=expected_name or None,
            source_brd=row.get("source_brd", "").strip() or None,
        )
        db.add(case)
        imported += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "catalog_missing": catalog_missing}
