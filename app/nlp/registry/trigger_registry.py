# Trigger registry — in sync with app/llm/schemas.py ALLOWED_TRIGGERS

VALID_TRIGGERS = {
    # Generic / Finance
    "loan_requested",
    "payment_due",
    "payment_missed",
    "delivery_failed",
    "account_locked",
    "fraud_detected",

    # Support
    "ticket_created",
    "ticket_unresolved",
    "sla_breached",
    "complaint_created",
    "complaint_escalated",
    "customer_churned",
    "refund_requested",
    "survey_completed",

    # Health
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
