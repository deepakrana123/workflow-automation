# Action registry — in sync with app/llm/schemas.py ALLOWED_ACTIONS

VALID_ACTIONS = {
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

    # Support
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

    # Health
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
