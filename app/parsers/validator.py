# ── ALLOWED TRIGGERS ─────────────────────────────────────────────────────────
# Generic + Support + Health domains
# Must stay in sync with: llm/schemas.py, llm/prompts/parser_v1.txt

ALLOWED_TRIGGERS = {
    # Generic / Finance
    "loan_requested",
    "payment_due",
    "payment_missed",
    "delivery_failed",
    "account_locked",
    "fraud_detected",

    # Support domain
    "ticket_created",
    "ticket_unresolved",
    "sla_breached",
    "complaint_created",
    "complaint_escalated",
    "customer_churned",
    "refund_requested",
    "survey_completed",

    # Health domain
    "patient_admitted",
    "patient_discharged",
    "lab_result_ready",
    "appointment_missed",
    "medication_overdue",
    "critical_vitals",
    "insurance_approved",
    "insurance_denied",
    "followup_due",
}


# ── ALLOWED ACTIONS ───────────────────────────────────────────────────────────
# Generic + Support + Health domains
# Must stay in sync with: llm/schemas.py, llm/prompts/parser_v1.txt, dispatcher.py

ALLOWED_ACTIONS = {
    # Generic
    "send_reminder",
    "escalate_case",
    "assign_senior_officer",
    "close_case",
    "reject_loan",
    "notify_manager",
    "validate_payment",
    "send_email_notification",
    "send_sms_notification",
    "send_push_notification",
    "create_audit_record",
    "trigger_webhook",
    "update_entity_status",
    "flag_for_review",
    "lock_account",
    "unlock_account",
    "generate_report",

    # Support domain
    "create_support_ticket",
    "assign_support_agent",
    "escalate_to_tier2",
    "send_sla_breach_alert",
    "send_customer_update",
    "resolve_ticket",
    "send_satisfaction_survey",
    "process_refund",
    "flag_repeat_complaint",
    "close_ticket_no_response",

    # Health domain
    "schedule_appointment",
    "send_medication_reminder",
    "alert_care_team",
    "escalate_to_specialist",
    "notify_lab_result",
    "trigger_emergency_protocol",
    "send_discharge_instructions",
    "flag_high_risk_patient",
    "request_insurance_approval",
    "send_wellness_check",
}


def validate_rule(rule: dict):
    errors = []

    if not rule.get("trigger"):
        errors.append("trigger is required")
    if not rule.get("action"):
        errors.append("action is required")

    if rule.get("trigger") and rule["trigger"] not in ALLOWED_TRIGGERS:
        errors.append(f"invalid trigger: {rule['trigger']!r}")

    if rule.get("action") and rule["action"] not in ALLOWED_ACTIONS:
        errors.append(f"invalid action: {rule['action']!r}")

    delay = rule.get("delay_days")
    if delay is not None:
        if not isinstance(delay, int):
            errors.append("delay_days must be integer")
        elif delay < 0:
            errors.append("delay_days cannot be negative")
        elif delay > 365:
            errors.append("delay_days too large")

    if not isinstance(rule.get("conditions", []), list):
        errors.append("conditions must be list")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
    }
