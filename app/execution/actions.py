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
