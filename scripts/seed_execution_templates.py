"""
scripts/seed_execution_templates.py

Sets execution_template on every ActionDefinition row based on handler type.

Classification rules (mirrors python_executor.py docstring):
  - PYTHON: calculations, document generation, internal state operations.
            All must have a matching entry in ACTION_HANDLER_MAP.
  - HTTP  : everything else — business operations that call an external service.
            base_url is set to http://localhost:8000/api so every action routes
            to the built-in mock server by default (/api/mock/{action_name}).
            For production: update base_url on the ActionDefinition row, or
            set a workspace-local execution_template via the unmapped-action
            resolution flow (WorkflowActionMapping snapshot).

Run once after seeding action_definitions:
    python scripts/seed_execution_templates.py

Safe to re-run — uses UPDATE … WHERE execution_template IS NULL so already-set
rows are left untouched. Add --force to overwrite all rows.
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal
from app.models.action_definitions import ActionDefinition
from app.execution.python.action_handler_registry import ACTION_HANDLER_MAP

# ── Python actions — pure in-process only ────────────────────────────────────
# Calculations, document generation, OCR (future). No network calls.
PYTHON_ACTIONS = {
    # Financial calculations
    "calculate_emi", "calculate_risk_score", "calculate_tax",
    "calculate_credit_score", "calculate_ltv_ratio", "calculate_interest",
    "calculate_interest_rate", "calculate_eligibility",
    "calculate_loan_eligibility", "calculate_foreclosure_amount",
    "calculate_prepayment_charges", "calculate_penal_interest",
    "calculate_rd_maturity", "calculate_fd_interest", "calculate_alm_gap",
    "calculate_eblr", "calculate_mclr", "calculate_debt_service_ratio",
    "calculate_group_utilization", "calculate_hedge_effectiveness",
    "calculate_mark_to_market", "calculate_account_balance",
    "calculate_forex_margin", "calculate_penalty_on_premature_withdrawal",
    "calculate_provision_coverage",
    "recalculate_emi",
    "compute_ecl", "compute_gst", "compute_provisioning",
    "compute_depreciation", "compute_drawing_power", "compute_cost_of_funds",
    "compute_interest_on_interest", "compute_internal_rating",
    "compute_nii", "compute_recovery_progress",
    # Document generation
    "generate_pdf", "generate_csv", "generate_excel",
    "generate_repayment_schedule", "generate_loan_agreement",
    "generate_interest_certificate",
}


def _python_template(name: str) -> dict:
    return {
        "execution_type": "python",
        "configuration": {
            "handler":     name,
            "description": "Pure Python in-process handler. No external call.",
        },
    }


def _http_template(name: str) -> dict:
    return {
        "execution_type": "http",
        "configuration": {
            "base_url": "http://localhost:8000/api",
            "method":   "POST",
            "endpoint": f"/mock/{name}",
            "timeout":  30,
            "headers": {
                "Content-Type": "application/json",
                "X-Action":     name,
            },
            "body_template": {
                "entity_id":   "{{entity_id}}",
                "action":      name,
                "workflow_id": "{{workflow_id}}",
            },
            "response_mapping": {
                "status":    "$.status",
                "reference": "$.reference_id",
                "message":   "$.message",
            },
        },
    }


def run(force: bool = False) -> None:
    db = SessionLocal()
    try:
        query = db.query(ActionDefinition)
        if not force:
            query = query.filter(ActionDefinition.execution_template.is_(None))

        rows = query.all()
        print(f"Processing {len(rows)} ActionDefinition rows "
              f"({'all' if force else 'missing execution_template only'})…")

        python_count = http_count = 0

        for ad in rows:
            # ACTION_HANDLER_MAP is the single source of truth for what is
            # a local Python handler. If the name is registered there, it
            # must run via PythonExecutor — regardless of what the old seed
            # may have written. Everything not in the map goes to HttpExecutor.
            if ad.name in ACTION_HANDLER_MAP:
                ad.execution_template = _python_template(ad.name)
                python_count += 1
            else:
                ad.execution_template = _http_template(ad.name)
                http_count += 1

        db.commit()
        print(f"\nDone. python={python_count}  http={http_count}")

    except Exception as exc:
        db.rollback()
        print(f"ERROR: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed execution_template on ActionDefinition rows")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing execution_template values")
    args = parser.parse_args()
    run(force=args.force)
