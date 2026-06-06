def normalize(text: str) -> str:
    return text.lower().strip()


# ── ACTION PATTERNS ───────────────────────────────────────────────────────────
# Generic + Support + Health domains

ACTION_PATTERNS = {

    # ── Generic ──────────────────────────────────────────────────────────────
    "send_reminder": [
        "remind", "send reminder", "notify customer", "send notification",
    ],
    "escalate_case": [
        "escalate", "raise to manager", "send to supervisor", "escalation",
    ],
    "assign_senior_officer": [
        "assign senior officer", "assign to senior", "assign to manager",
    ],
    "close_case": [
        "close case", "resolve ticket", "close ticket",
    ],
    "reject_loan": [
        "reject loan", "reject application", "decline loan",
    ],
    "notify_manager": [
        "notify manager", "alert manager", "inform manager",
    ],
    "send_email_notification": [
        "send email", "email notification", "email customer", "email alert",
    ],
    "send_sms_notification": [
        "send sms", "sms notification", "text customer", "text message",
    ],
    "send_push_notification": [
        "push notification", "send push", "app notification",
    ],
    "create_audit_record": [
        "create audit", "audit record", "log event", "compliance record",
    ],
    "trigger_webhook": [
        "trigger webhook", "call webhook", "send webhook", "notify external",
    ],
    "update_entity_status": [
        "update status", "change status", "set status",
    ],
    "flag_for_review": [
        "flag for review", "flag case", "mark for review", "manual review",
    ],
    "lock_account": [
        "lock account", "freeze account", "suspend account",
    ],
    "unlock_account": [
        "unlock account", "unfreeze account", "restore account",
    ],
    "validate_payment": [
        "validate payment", "payment validation", "verify payment", "check payment",
    ],

    # ── Support domain ────────────────────────────────────────────────────────
    "create_support_ticket": [
        "create ticket", "open ticket", "raise ticket", "new support ticket",
    ],
    "assign_support_agent": [
        "assign agent", "assign support", "route to agent",
    ],
    "escalate_to_tier2": [
        "escalate tier2", "tier 2 escalation", "second level support",
    ],
    "send_sla_breach_alert": [
        "sla breach", "sla alert", "breach alert", "sla warning",
    ],
    "send_customer_update": [
        "customer update", "update customer", "status update to customer",
    ],
    "resolve_ticket": [
        "resolve ticket", "mark resolved", "ticket resolved",
    ],
    "send_satisfaction_survey": [
        "satisfaction survey", "csat survey", "nps survey", "send survey",
    ],
    "process_refund": [
        "process refund", "issue refund", "refund customer",
    ],
    "flag_repeat_complaint": [
        "flag repeat", "repeat complaint", "frequent complainer",
    ],
    "close_ticket_no_response": [
        "close no response", "auto close", "no response close",
    ],

    # ── Health domain ─────────────────────────────────────────────────────────
    "schedule_appointment": [
        "schedule appointment", "book appointment", "create appointment",
    ],
    "send_medication_reminder": [
        "medication reminder", "medicine reminder", "drug reminder",
    ],
    "alert_care_team": [
        "alert care team", "notify care team", "care team alert",
    ],
    "escalate_to_specialist": [
        "escalate specialist", "refer specialist", "specialist referral",
    ],
    "notify_lab_result": [
        "lab result", "test result", "notify lab", "lab notification",
    ],
    "trigger_emergency_protocol": [
        "emergency protocol", "code blue", "emergency alert", "critical alert",
    ],
    "send_discharge_instructions": [
        "discharge instructions", "discharge patient", "post discharge",
    ],
    "flag_high_risk_patient": [
        "high risk patient", "flag patient", "risk flag patient",
    ],
    "request_insurance_approval": [
        "insurance approval", "pre authorization", "insurance request",
    ],
    "generate_report": [
        "generate report", "create report", "produce report",
    ],
    "send_wellness_check": [
        "wellness check", "health check", "patient check in",
    ],
}


# ── TRIGGER PATTERNS ──────────────────────────────────────────────────────────
# Generic + Support + Health domains

TRIGGER_PATTERNS = {

    # ── Generic / Finance ─────────────────────────────────────────────────────
    "loan_requested": [
        "loan request", "loan applied", "apply loan", "loan application",
    ],
    "payment_due": [
        "payment due", "emi due", "due payment", "bill due",
    ],
    "payment_missed": [
        "missed emi", "payment missed", "missed payment", "overdue payment",
    ],
    "delivery_failed": [
        "delivery failed", "order failed", "shipment failed",
    ],
    "account_locked": [
        "account locked", "account frozen", "account suspended",
    ],
    "fraud_detected": [
        "fraud detected", "suspicious activity", "fraud alert",
    ],

    # ── Support domain ────────────────────────────────────────────────────────
    "ticket_created": [
        "ticket created", "ticket raised", "new ticket", "issue created",
        "ticket", "tickets", "support request",
    ],
    "ticket_unresolved": [
        "ticket unresolved", "unresolved ticket", "open ticket",
    ],
    "sla_breached": [
        "sla breached", "sla breach", "sla violated", "sla exceeded",
    ],
    "complaint_created": [
        "complaint created", "complaint raised", "new complaint",
    ],
    "complaint_escalated": [
        "complaint escalated", "escalated complaint",
    ],
    "customer_churned": [
        "customer churned", "customer left", "churn detected",
    ],
    "refund_requested": [
        "refund requested", "refund request", "customer refund",
    ],
    "survey_completed": [
        "survey completed", "csat completed", "nps submitted",
    ],

    # ── Health domain ─────────────────────────────────────────────────────────
    "patient_admitted": [
        "patient admitted", "admission", "patient registered",
    ],
    "patient_discharged": [
        "patient discharged", "discharge", "patient released",
    ],
    "lab_result_ready": [
        "lab result ready", "test result ready", "results available",
    ],
    "appointment_missed": [
        "appointment missed", "missed appointment", "no show",
    ],
    "medication_overdue": [
        "medication overdue", "missed medication", "medication missed",
    ],
    "critical_vitals": [
        "critical vitals", "abnormal vitals", "vitals alert",
    ],
    "insurance_approved": [
        "insurance approved", "pre auth approved", "authorization approved",
    ],
    "insurance_denied": [
        "insurance denied", "pre auth denied", "authorization denied",
    ],
    "followup_due": [
        "followup due", "follow up due", "checkup due",
    ],
}


# ── INFERENCE MAP ─────────────────────────────────────────────────────────────

def infer_trigger_from_action(action: str):
    """
    Single source of truth for action → trigger inference.
    Used by intent_mapper, rule_builder, and orchestrator.
    """
    _map = {
        # Generic
        "send_reminder":          "payment_due",
        "escalate_case":          "complaint_created",
        "assign_senior_officer":  "ticket_created",
        "close_case":             "ticket_created",
        "reject_loan":            "loan_requested",
        "notify_manager":         "loan_requested",
        "send_email_notification":"payment_due",
        "send_sms_notification":  "payment_due",
        "send_push_notification": "payment_due",
        "create_audit_record":    "fraud_detected",
        "trigger_webhook":        "ticket_created",
        "update_entity_status":   "ticket_created",
        "flag_for_review":        "fraud_detected",
        "lock_account":           "fraud_detected",
        "unlock_account":         "account_locked",
        "generate_report":        "ticket_unresolved",
        "validate_payment":       "payment_due",

        # Support
        "create_support_ticket":    "complaint_created",
        "assign_support_agent":     "ticket_created",
        "escalate_to_tier2":        "sla_breached",
        "send_sla_breach_alert":    "sla_breached",
        "send_customer_update":     "ticket_created",
        "resolve_ticket":           "ticket_unresolved",
        "send_satisfaction_survey": "survey_completed",
        "process_refund":           "refund_requested",
        "flag_repeat_complaint":    "complaint_created",
        "close_ticket_no_response": "ticket_unresolved",

        # Health
        "schedule_appointment":       "followup_due",
        "send_medication_reminder":   "medication_overdue",
        "alert_care_team":            "critical_vitals",
        "escalate_to_specialist":     "critical_vitals",
        "notify_lab_result":          "lab_result_ready",
        "trigger_emergency_protocol": "critical_vitals",
        "send_discharge_instructions":"patient_discharged",
        "flag_high_risk_patient":     "patient_admitted",
        "request_insurance_approval": "patient_admitted",
        "send_wellness_check":        "followup_due",
    }
    return _map.get(action)


# ── MATCHING FUNCTIONS ────────────────────────────────────────────────────────

def map_action(text: str):
    text = normalize(text)
    for action, patterns in ACTION_PATTERNS.items():
        for pattern in patterns:
            words = pattern.split()
            if all(word in text for word in words):
                return {"action": action, "confidence": 0.95}
    return {"action": None, "confidence": 0.0}


def map_trigger(text: str):
    text = normalize(text)
    for trigger, phrases in TRIGGER_PATTERNS.items():
        for pattern in phrases:
            words = pattern.split()
            if all(word in text for word in words):
                return {"trigger": trigger, "confidence": 0.9}
    return {"trigger": None, "confidence": 0.0}


def map_intents(text: str):
    action_result  = map_action(text)
    trigger_result = map_trigger(text)

    if trigger_result["trigger"] is None and action_result["action"]:
        trigger_result = {
            "trigger": infer_trigger_from_action(action_result["action"]),
            "confidence": 0.6,
        }

    return {
        "action_result": action_result,
        "trigger_result": trigger_result,
    }
