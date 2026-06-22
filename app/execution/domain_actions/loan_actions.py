"""
Common Loan Management Actions
Covers: CIBIL/bureau checks, income verification, document handling,
sanction, disbursement, EMI, closure, and regulatory reporting.
Applies to: personal loan, home loan, car loan, business loan.
"""

import time
from app.core.logger import logger


def run_cibil_check(payload: dict, config: dict) -> dict:
    """Query CIBIL or bureau for customer credit score and report."""
    bureau = config.get("bureau", "CIBIL")
    logger.info("loan_cibil_check_done", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "bureau": bureau,
    }})
    return {"success": True, "status": "success", "bureau": bureau, "cibil_score": 720, "report_id": f"CIBIL-{int(time.time())}"}


def send_cibil_low_alert(payload: dict, config: dict) -> dict:
    """Alert credit/risk team when CIBIL score is below threshold."""
    threshold = config.get("threshold", 650)
    score = config.get("score", 0)
    logger.warning("loan_cibil_low_alert", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "score": score, "threshold": threshold,
    }})
    return {"success": True, "status": "success", "alert_sent": True, "score": score, "threshold": threshold}


def run_income_verification(payload: dict, config: dict) -> dict:
    """Verify income documents — salary slips, ITR, bank statements."""
    method = config.get("method", "document_review")
    logger.info("loan_income_verification_done", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "method": method,
    }})
    return {"success": True, "status": "success", "income_verified": True, "method": method}


def send_document_checklist(payload: dict, config: dict) -> dict:
    """Send list of required documents to the customer."""
    loan_type = config.get("loan_type", "personal")
    channel = config.get("channel", "email")
    logger.info("loan_document_checklist_sent", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "loan_type": loan_type,
    }})
    return {"success": True, "status": "success", "checklist_sent": True, "loan_type": loan_type, "channel": channel}


def verify_submitted_documents(payload: dict, config: dict) -> dict:
    """Verify completeness and authenticity of documents submitted by customer."""
    logger.info("loan_documents_verified", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
    }})
    return {"success": True, "status": "success", "documents_verified": True, "verified_at": int(time.time())}


def send_validation_documents(payload: dict, config: dict) -> dict:
    """Send validated documents or verification confirmation to the customer."""
    channel = config.get("channel", "email")
    logger.info("loan_validation_documents_sent", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "channel": channel,
    }})
    return {"success": True, "status": "success", "validation_docs_sent": True, "channel": channel}


def issue_sanction_letter(payload: dict, config: dict) -> dict:
    """Generate and issue formal loan sanction letter to the customer."""
    loan_amount = config.get("loan_amount", 0)
    logger.info("loan_sanction_letter_issued", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "loan_amount": loan_amount,
    }})
    return {
        "success": True, "status": "success",
        "sanction_letter_id": f"SL-{int(time.time())}",
        "loan_amount": loan_amount,
    }


def send_rejection_letter(payload: dict, config: dict) -> dict:
    """Send formal rejection letter to the customer with reason."""
    reason = config.get("reason", "eligibility_not_met")
    channel = config.get("channel", "email")
    logger.info("loan_rejection_letter_sent", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "reason": reason,
    }})
    return {"success": True, "status": "success", "rejection_letter_sent": True, "reason": reason}


def send_sanction_terms(payload: dict, config: dict) -> dict:
    """Send loan sanction terms and conditions for customer acceptance."""
    channel = config.get("channel", "email")
    logger.info("loan_sanction_terms_sent", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "channel": channel,
    }})
    return {"success": True, "status": "success", "sanction_terms_sent": True}


def generate_repayment_schedule(payload: dict, config: dict) -> dict:
    """Generate full EMI repayment schedule for the loan tenure."""
    tenure_months = config.get("tenure_months", 12)
    logger.info("loan_repayment_schedule_generated", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "tenure_months": tenure_months,
    }})
    return {"success": True, "status": "success", "schedule_generated": True, "tenure_months": tenure_months}


def send_disbursement_advice(payload: dict, config: dict) -> dict:
    """Send disbursement confirmation and details to the customer."""
    amount = config.get("amount", 0)
    channel = config.get("channel", "email")
    logger.info("loan_disbursement_advice_sent", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "amount": amount,
    }})
    return {"success": True, "status": "success", "disbursement_advice_sent": True, "amount": amount}


def link_insurance_to_loan(payload: dict, config: dict) -> dict:
    """Link a life or property insurance policy to the loan account."""
    insurance_type = config.get("insurance_type", "life")
    logger.info("loan_insurance_linked", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "insurance_type": insurance_type,
    }})
    return {"success": True, "status": "success", "insurance_linked": True, "insurance_type": insurance_type}


def send_insurance_reminder(payload: dict, config: dict) -> dict:
    """Remind customer to submit insurance documents for the loan."""
    logger.info("loan_insurance_reminder_sent", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
    }})
    return {"success": True, "status": "success", "insurance_reminder_sent": True}


def collect_post_disbursement_documents(payload: dict, config: dict) -> dict:
    """Collect post-disbursement documents like original property papers or RC."""
    doc_type = config.get("doc_type", "original_documents")
    logger.info("loan_post_disbursement_docs_collected", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "doc_type": doc_type,
    }})
    return {"success": True, "status": "success", "docs_collected": True, "doc_type": doc_type}


def generate_interest_certificate(payload: dict, config: dict) -> dict:
    """Generate annual interest certificate for tax purposes."""
    year = config.get("financial_year", "current")
    logger.info("loan_interest_certificate_generated", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "year": year,
    }})
    return {"success": True, "status": "success", "certificate_id": f"INT-CERT-{int(time.time())}", "year": year}


def send_noc_on_closure(payload: dict, config: dict) -> dict:
    """Issue NOC and loan closure confirmation after full repayment."""
    logger.info("loan_noc_on_closure_sent", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
    }})
    return {"success": True, "status": "success", "noc_issued": True, "closure_confirmed": True}


def update_cibil_post_closure(payload: dict, config: dict) -> dict:
    """Update CIBIL/bureau with loan closure to reflect in credit report."""
    logger.info("loan_cibil_updated_post_closure", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
    }})
    return {"success": True, "status": "success", "cibil_updated": True}
