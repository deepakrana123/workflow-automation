"""
Generic / cross-domain actions.
Domain-specific actions live in domain_actions/support_actions.py
and domain_actions/health_actions.py.
"""

import random
import time
from app.core.logger import logger


# ── Existing actions ──────────────────────────────────────────────────────────

def send_reminder(payload, config):
    channel = config.get("channel", "email")
    logger.info("action_send_reminder_success", extra={"extra_data": {
        "payload": payload, "channel": channel,
    }})
    return {"success": True, "status": "success", "message": "reminder sent", "channel": channel}


def escalate_case(payload, config):
    logger.info("action_escalate_case_success", extra={"extra_data": {"payload": payload}})
    return {"success": True, "status": "success", "message": "case escalated"}


def assign_senior_officer(payload, config):
    officer_id = config.get("officer_id", "EMP101")
    logger.info("action_assign_senior_officer_success", extra={"extra_data": {
        "payload": payload, "officer_id": officer_id,
    }})
    return {"success": True, "status": "success", "officer_id": officer_id}


def notify_manager(payload, config):
    channel = config.get("channel", "email")
    logger.info("action_notify_manager_success", extra={"extra_data": {
        "payload": payload, "channel": channel,
    }})
    return {"success": True, "status": "success", "notified": True, "channel": channel}


def notify_customer(payload, config):
    channel = config.get("channel", "email")
    logger.info("action_notify_customer_success", extra={"extra_data": {
        "payload": payload, "channel": channel,
    }})
    return {"success": True, "status": "success", "notified": True, "channel": channel}


def close_case(payload, config):
    reason = config.get("reason", "resolved")
    logger.info("action_close_case_success", extra={"extra_data": {
        "payload": payload, "reason": reason,
    }})
    return {"success": True, "status": "success", "closed": True, "reason": reason}


def reject_loan(payload, config):
    reason = config.get("reason", "eligibility_failed")
    logger.info("action_reject_loan_success", extra={"extra_data": {
        "payload": payload, "reason": reason,
    }})
    return {"success": True, "status": "success", "rejected": True, "reason": reason}


def validate_payment_handler(payload, config):
    logger.info("action_validate_payment_success", extra={"extra_data": {"payload": payload}})
    return {"success": True, "status": "success", "validated": True}


def fail_randomly(payload, config):
    """Test action — fails 30% of the time to exercise retry logic."""
    if random.random() < 0.3:
        raise Exception("temporary failure")
    return {"success": True, "status": "success"}


# ── New generic actions ───────────────────────────────────────────────────────

def send_email_notification(payload, config):
    """Send a generic email notification."""
    template = config.get("template", "default")
    recipient = config.get("recipient", payload.get("entity_id", "unknown"))
    logger.info("action_send_email_success", extra={"extra_data": {
        "recipient": recipient, "template": template,
    }})
    return {"success": True, "status": "success", "template": template, "recipient": recipient}


def send_sms_notification(payload, config):
    """Send a generic SMS notification."""
    template = config.get("template", "default")
    logger.info("action_send_sms_success", extra={"extra_data": {"template": template}})
    return {"success": True, "status": "success", "template": template, "channel": "sms"}


def send_push_notification(payload, config):
    """Send a push notification to mobile app."""
    title = config.get("title", "Notification")
    logger.info("action_send_push_success", extra={"extra_data": {"title": title}})
    return {"success": True, "status": "success", "title": title, "channel": "push"}


def create_audit_record(payload, config):
    """Create an immutable audit record for compliance."""
    event_type = config.get("event_type", "generic_event")
    logger.info("action_audit_record_created", extra={"extra_data": {
        "event_type": event_type, "entity_id": payload.get("entity_id"),
    }})
    return {"success": True, "status": "success", "event_type": event_type, "recorded": True}


def trigger_webhook(payload, config):
    """Trigger an outbound webhook to an external system."""
    url = config.get("webhook_url", "https://example.com/webhook")
    logger.info("action_webhook_triggered", extra={"extra_data": {"url": url}})
    return {"success": True, "status": "success", "webhook_url": url, "triggered": True}


def update_entity_status(payload, config):
    """Update the status of an entity in the system."""
    new_status = config.get("new_status", "updated")
    entity_type = config.get("entity_type", "unknown")
    logger.info("action_entity_status_updated", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
        "entity_type": entity_type,
        "new_status": new_status,
    }})
    return {"success": True, "status": "success", "new_status": new_status}


def flag_for_review(payload, config):
    """Flag an entity for manual review."""
    reason = config.get("reason", "automated_flag")
    priority = config.get("priority", "normal")
    logger.info("action_flagged_for_review", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
        "reason": reason,
        "priority": priority,
    }})
    return {"success": True, "status": "success", "flagged": True, "reason": reason}


def lock_account(payload, config):
    """Lock a customer account (fraud, compliance, etc.)."""
    reason = config.get("reason", "security_hold")
    logger.warning("action_account_locked", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "reason": reason,
    }})
    return {"success": True, "status": "success", "locked": True, "reason": reason}


def unlock_account(payload, config):
    """Unlock a previously locked customer account."""
    logger.info("action_account_unlocked", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
    }})
    return {"success": True, "status": "success", "unlocked": True}


def generate_report(payload, config):
    """Generate a report for a workflow outcome."""
    report_type = config.get("report_type", "summary")
    logger.info("action_report_generated", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "report_type": report_type,
    }})
    return {
        "success": True, "status": "success",
        "report_type": report_type,
        "report_id": f"RPT-{int(time.time())}",
    }


# ── Finance domain actions ────────────────────────────────────────────────────

def approve_invoice(payload, config):
    """Approve, authorize, or validate an invoice for payment processing."""
    invoice_id = config.get("invoice_id", payload.get("entity_id", "unknown"))
    logger.info("action_approve_invoice_success", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "invoice_id": invoice_id,
    }})
    return {"success": True, "status": "success", "invoice_id": invoice_id, "approved": True}


def apply_credit(payload, config):
    """Apply credits, discounts, or adjustments to a customer account."""
    amount = config.get("credit_amount", 0)
    logger.info("action_apply_credit_success", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "amount": amount,
    }})
    return {"success": True, "status": "success", "credit_applied": True, "amount": amount}


def calculate_tax(payload, config):
    """Calculate tax, VAT, GST, or other tax liabilities for a transaction."""
    tax_type = config.get("tax_type", "standard")
    logger.info("action_calculate_tax_success", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "tax_type": tax_type,
    }})
    return {"success": True, "status": "success", "tax_calculated": True, "tax_type": tax_type}


def create_payment(payload, config):
    """Create, initiate, or execute a payment to a vendor, supplier, or customer."""
    amount = config.get("amount", 0)
    logger.info("action_create_payment_success", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "amount": amount,
    }})
    return {
        "success": True, "status": "success",
        "payment_id": f"PAY-{int(time.time())}",
        "amount": amount,
    }


def generate_financial_report(payload, config):
    """Generate a financial report, statement, or summary."""
    report_type = config.get("report_type", "financial_summary")
    logger.info("action_generate_financial_report_success", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "report_type": report_type,
    }})
    return {
        "success": True, "status": "success",
        "report_id": f"FIN-RPT-{int(time.time())}",
        "report_type": report_type,
    }


def notify_payment_failure(payload, config):
    """Notify customer or finance team about a failed or declined payment."""
    channel = config.get("channel", "email")
    logger.warning("action_notify_payment_failure_success", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "channel": channel,
    }})
    return {"success": True, "status": "success", "notified": True, "channel": channel}


def process_credit_check(payload, config):
    """Perform a credit check or creditworthiness assessment."""
    logger.info("action_process_credit_check_success", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
    }})
    return {"success": True, "status": "success", "credit_check_completed": True}


def reconcile_account(payload, config):
    """Reconcile account transactions, match payments to invoices."""
    logger.info("action_reconcile_account_success", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
    }})
    return {"success": True, "status": "success", "reconciled": True}


def send_audit_report(payload, config):
    """Send an audit report or compliance summary to stakeholders."""
    channel = config.get("channel", "email")
    logger.info("action_send_audit_report_success", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "channel": channel,
    }})
    return {"success": True, "status": "success", "report_sent": True, "channel": channel}


def send_invoice(payload, config):
    """Send, issue, or deliver an invoice to a customer or vendor."""
    channel = config.get("channel", "email")
    logger.info("action_send_invoice_success", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "channel": channel,
    }})
    return {
        "success": True, "status": "success",
        "invoice_id": f"INV-{int(time.time())}",
        "channel": channel,
    }


def send_payment_confirmation(payload, config):
    """Send payment confirmation, receipt, or acknowledgment."""
    channel = config.get("channel", "email")
    logger.info("action_send_payment_confirmation_success", extra={"extra_data": {
        "entity_id": payload.get("entity_id"), "channel": channel,
    }})
    return {"success": True, "status": "success", "confirmation_sent": True, "channel": channel}


def update_payment_method(payload, config):
    """Update, add, or modify a customer payment method."""
    logger.info("action_update_payment_method_success", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
    }})
    return {"success": True, "status": "success", "payment_method_updated": True}


def validate_transaction(payload, config):
    """Validate, verify, or authenticate a financial transaction."""
    logger.info("action_validate_transaction_success", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
    }})
    return {"success": True, "status": "success", "transaction_validated": True}


def verify_compliance(payload, config):
    """Verify compliance with regulations, KYC, AML, or other requirements."""
    logger.info("action_verify_compliance_success", extra={"extra_data": {
        "entity_id": payload.get("entity_id"),
    }})
    return {"success": True, "status": "success", "compliance_verified": True}
