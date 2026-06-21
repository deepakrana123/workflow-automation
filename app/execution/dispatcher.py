import os
from app.execution.actions import (
    send_reminder, escalate_case, assign_senior_officer,
    notify_manager, notify_customer, close_case, reject_loan, validate_payment_handler,
    send_email_notification, send_sms_notification, send_push_notification,
    create_audit_record, trigger_webhook, update_entity_status,
    flag_for_review, lock_account, unlock_account, generate_report,
    fail_randomly,
    # Finance domain
    approve_invoice, apply_credit, calculate_tax, create_payment,
    generate_financial_report, notify_payment_failure, process_credit_check,
    reconcile_account, send_audit_report, send_invoice,
    send_payment_confirmation, update_payment_method,
    validate_transaction, verify_compliance,
)
from app.execution.domain_actions.support_actions import (
    create_support_ticket, assign_support_agent, escalate_to_tier2,
    send_sla_breach_alert, send_customer_update, resolve_ticket,
    send_satisfaction_survey, process_refund, flag_repeat_complaint,
    close_ticket_no_response,
)
from app.execution.domain_actions.health_actions import (
    schedule_appointment, send_medication_reminder, alert_care_team,
    escalate_to_specialist, notify_lab_result, trigger_emergency_protocol,
    send_discharge_instructions, flag_high_risk_patient,
    request_insurance_approval, send_wellness_check,
)
from app.execution.chaos_actions import (
    chaos_send_reminder, chaos_escalate_case, chaos_notify_manager,
    chaos_reject_loan, chaos_close_case, chaos_assign_senior_officer,
    _apply_chaos, _chaos_response,
)
from app.core.logger import logger


# ── PRODUCTION ACTION MAP ─────────────────────────────────────────────────────
# Keys = exact action names the LLM must use (enforced by prompt).
# This is the canonical registry — one entry per real function.

_PRODUCTION_ACTION_MAP = {
    # Generic / Finance
    "send_reminder":           send_reminder,
    "escalate_case":           escalate_case,
    "assign_senior_officer":   assign_senior_officer,
    "notify_manager":          notify_manager,
    "notify_customer":         notify_customer,
    "close_case":              close_case,
    "reject_loan":             reject_loan,
    "validate_payment":        validate_payment_handler,
    "send_email_notification": send_email_notification,
    "send_sms_notification":   send_sms_notification,
    "send_push_notification":  send_push_notification,
    "create_audit_record":     create_audit_record,
    "trigger_webhook":         trigger_webhook,
    "update_entity_status":    update_entity_status,
    "flag_for_review":         flag_for_review,
    "lock_account":            lock_account,
    "unlock_account":          unlock_account,
    "generate_report":         generate_report,
    "fail_randomly":           fail_randomly,

    # Finance domain
    "approve_invoice":             approve_invoice,
    "apply_credit":                apply_credit,
    "calculate_tax":               calculate_tax,
    "create_payment":              create_payment,
    "generate_financial_report":   generate_financial_report,
    "notify_payment_failure":      notify_payment_failure,
    "process_credit_check":        process_credit_check,
    "reconcile_account":           reconcile_account,
    "send_audit_report":           send_audit_report,
    "send_invoice":                send_invoice,
    "send_payment_confirmation":   send_payment_confirmation,
    "update_payment_method":       update_payment_method,
    "validate_transaction":        validate_transaction,
    "verify_compliance":           verify_compliance,

    # Support domain
    "create_support_ticket":    create_support_ticket,
    "assign_support_agent":     assign_support_agent,
    "escalate_to_tier2":        escalate_to_tier2,
    "send_sla_breach_alert":    send_sla_breach_alert,
    "send_customer_update":     send_customer_update,
    "resolve_ticket":           resolve_ticket,
    "send_satisfaction_survey": send_satisfaction_survey,
    "process_refund":           process_refund,
    "flag_repeat_complaint":    flag_repeat_complaint,
    "close_ticket_no_response": close_ticket_no_response,

    # Health domain
    "schedule_appointment":        schedule_appointment,
    "send_medication_reminder":    send_medication_reminder,
    "alert_care_team":             alert_care_team,
    "escalate_to_specialist":      escalate_to_specialist,
    "notify_lab_result":           notify_lab_result,
    "trigger_emergency_protocol":  trigger_emergency_protocol,
    "send_discharge_instructions": send_discharge_instructions,
    "flag_high_risk_patient":      flag_high_risk_patient,
    "request_insurance_approval":  request_insurance_approval,
    "send_wellness_check":         send_wellness_check,
}


def _resolve_handler_from_db(action_name: str):
    """
    DB fallback — looks up action by name in action_definitions.
    If the row has a handler_name, resolve that to a function in _PRODUCTION_ACTION_MAP.
    This allows DB aliases to map to canonical handlers without code changes.
    """
    try:
        from app.db.session import SessionLocal
        from app.models.action_definitions import ActionDefinition
        db = SessionLocal()
        try:
            row = db.query(ActionDefinition).filter(
                ActionDefinition.name == action_name,
                ActionDefinition.active == True,
            ).first()
            if row and row.handler_name:
                return _PRODUCTION_ACTION_MAP.get(row.handler_name)
        finally:
            db.close()
    except Exception as e:
        logger.warning(
            "dispatcher_db_fallback_failed",
            extra={"extra_data": {"action_name": action_name, "error": str(e)}},
        )
    return None



def _make_chaos_action(action_name: str):
    """Factory — wraps any action name with the chaos engine."""
    def _chaos(payload: dict, config: dict) -> dict:
        _apply_chaos(action_name, payload, config)
        return _chaos_response(action_name)
    _chaos.__name__ = f"chaos_{action_name}"
    return _chaos


_CHAOS_ACTION_MAP = {
    name: _make_chaos_action(name)
    for name in _PRODUCTION_ACTION_MAP
}

# Override specific chaos actions with hand-crafted versions where needed
_CHAOS_ACTION_MAP.update({
    "send_reminder":         chaos_send_reminder,
    "escalate_case":         chaos_escalate_case,
    "assign_senior_officer": chaos_assign_senior_officer,
    "notify_manager":        chaos_notify_manager,
    "reject_loan":           chaos_reject_loan,
    "close_case":            chaos_close_case,
    "fail_randomly":         fail_randomly,
})


# ── DISPATCHER ────────────────────────────────────────────────────────────────

_CHAOS_ENABLED = os.getenv("CHAOS_MODE", "false").lower() == "true"
ACTION_MAP = _CHAOS_ACTION_MAP if _CHAOS_ENABLED else _PRODUCTION_ACTION_MAP


def execute_action(action_name: str, payload: dict, config: dict) -> dict:
    handler = ACTION_MAP.get(action_name)

    # DB fallback — resolve via handler_name column in action_definitions
    if not handler:
        handler = _resolve_handler_from_db(action_name)
        if handler:
            logger.info(
                "action_resolved_via_db",
                extra={"extra_data": {"action_name": action_name}},
            )

    if not handler:
        logger.error(
            "action_unknown",
            extra={"extra_data": {
                "action_name": action_name,
                "chaos_enabled": _CHAOS_ENABLED,
                "available_actions": sorted(ACTION_MAP.keys()),
            }},
        )
        return {
            "success": False,
            "status": "failed",
            "action": action_name,
            "reason": "unknown_action",
            "skip_retry": True,
        }

    logger.info(
        "action_dispatched",
        extra={"extra_data": {
            "action_name": action_name,
            "chaos_enabled": _CHAOS_ENABLED,
            "chaos_mode": config.get("chaos_mode", "none") if _CHAOS_ENABLED else "disabled",
        }},
    )

    try:
        result = handler(payload, config)
    except Exception as e:
        logger.warning(
            "action_raised_exception",
            extra={"extra_data": {"action_name": action_name, "error": str(e)}},
        )
        raise

    if result.get("status") == "success" or result.get("success"):
        logger.info("action_success", extra={"extra_data": {"action_name": action_name}})
    else:
        logger.warning("action_failed", extra={"extra_data": {
            "action_name": action_name, "result": result,
        }})

    return result
