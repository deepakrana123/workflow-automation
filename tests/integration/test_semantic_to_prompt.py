import pytest


from app.db.session import SessionLocal
from app.nlp.catalog.matcher import CatalogMatcher
from app.nlp.catalog.triggerRepository import TriggerDefinitionRepository
from app.nlp.catalog.actionRepository import ActionDefinitionRepository
from app.nlp.suitability.suitability_agent import SuitabilityAgent
from app.nlp.prompts.builder import PromptBuilder
from app.nlp.prompts.prompt_context import PromptContext
from app.semantic.semantic_catalog_retriever import SemanticCatalogRetriever


# Format: (query, expected_name, domain, description)
# expected_name = trigger or action name that MUST appear in the result
CASES = [

    # ── Finance — Trigger synonyms ────────────────────────────────────────────
    ("invoice still unpaid",                    "payment_missed",   "finance",  "payment_missed via invoice language"),
    ("payment was not received",                "payment_missed",   "finance",  "payment_missed via passive phrasing"),
    ("bill is past due",                        "payment_due",      "finance",  "payment_due via bill language"),
    ("installment coming up",                   "payment_due",      "finance",  "payment_due via installment"),
    ("emi is overdue",                          "payment_missed",   "finance",  "payment_missed via emi"),
    ("suspicious account activity",             "fraud_detected",   "finance",  "fraud_detected via suspicious activity"),
    ("fraudulent transaction detected",         "fraud_detected",   "finance",  "fraud_detected via transaction"),
    ("unauthorized access to account",          "fraud_detected",   "finance",  "fraud_detected via unauthorized access"),
    ("profile has been blocked",                "account_locked",   "finance",  "account_locked via blocked"),
    ("user account suspended",                  "account_locked",   "finance",  "account_locked via suspended"),
    ("new borrowing request submitted",         "loan_requested",   "finance",  "loan_requested via borrowing request"),
    ("loan application arrived",                "loan_requested",   "finance",  "loan_requested via application"),
    ("credit request received",                 "loan_requested",   "finance",  "loan_requested via credit request"),
    ("package not delivered",                   "delivery_failed",  "finance",  "delivery_failed via package"),
    ("shipment failed",                         "delivery_failed",  "finance",  "delivery_failed via shipment"),

    # ── Finance — Action synonyms ─────────────────────────────────────────────
    ("freeze customer account",                 "lock_account",         "finance",  "lock_account via freeze"),
    ("suspend the account",                     "lock_account",         "finance",  "lock_account via suspend"),
    ("unblock the account",                     "unlock_account",       "finance",  "unlock_account via unblock"),
    ("restore account access",                  "unlock_account",       "finance",  "unlock_account via restore"),
    ("mark for investigation",                  "flag_for_review",      "finance",  "flag_for_review via investigation"),
    ("tag as suspicious",                       "flag_for_review",      "finance",  "flag_for_review via suspicious tag"),
    ("create audit trail",                      "create_audit_record",  "finance",  "create_audit_record via audit trail"),
    ("log compliance record",                   "create_audit_record",  "finance",  "create_audit_record via compliance"),
    ("tell the manager right away",             "notify_manager",       "finance",  "notify_manager via tell manager"),
    ("alert supervisor about this",             "notify_manager",       "finance",  "notify_manager via alert supervisor"),
    ("escalate this to higher authority",       "escalate_case",        "finance",  "escalate_case via authority"),
    ("send payment warning to customer",        "send_reminder",        "finance",  "send_reminder via payment warning"),
    ("remind customer about payment",           "send_reminder",        "finance",  "send_reminder via remind"),

    # ── Support — Trigger synonyms ────────────────────────────────────────────
    ("new issue was opened",                    "ticket_created",       "support",  "ticket_created via issue opened"),
    ("support request submitted",               "ticket_created",       "support",  "ticket_created via support request"),
    ("complaint filed by customer",             "complaint_created",    "support",  "complaint_created via complaint filed"),
    ("customer raised a grievance",             "complaint_created",    "support",  "complaint_created via grievance"),
    ("service level agreement violated",        "sla_breached",         "support",  "sla_breached via violated"),
    ("response time exceeded",                  "sla_breached",         "support",  "sla_breached via response time"),
    ("customer wants money back",               "refund_requested",     "support",  "refund_requested via money back"),
    ("refund needed for order",                 "refund_requested",     "support",  "refund_requested via order refund"),
    ("client stopped using service",            "customer_churned",     "support",  "customer_churned via stopped using"),
    ("customer cancelled subscription",         "customer_churned",     "support",  "customer_churned via cancelled"),
    ("ticket has not been closed",              "ticket_unresolved",    "support",  "ticket_unresolved via not closed"),
    ("issue still pending",                     "ticket_unresolved",    "support",  "ticket_unresolved via pending"),

    # ── Support — Action synonyms ─────────────────────────────────────────────
    ("assign employee to ticket",               "assign_support_agent", "support",  "assign_support_agent via employee"),
    ("route ticket to an agent",                "assign_support_agent", "support",  "assign_support_agent via route"),
    ("move to second level support",            "escalate_to_tier2",    "support",  "escalate_to_tier2 via second level"),
    ("push to tier two team",                   "escalate_to_tier2",    "support",  "escalate_to_tier2 via tier two"),
    ("inform customer about update",            "send_customer_update", "support",  "send_customer_update via inform"),
    ("mark ticket as done",                     "resolve_ticket",       "support",  "resolve_ticket via mark done"),
    ("fix the support issue",                   "resolve_ticket",       "support",  "resolve_ticket via fix"),
    ("give customer a refund",                  "process_refund",       "support",  "process_refund via give refund"),
    ("initiate money return",                   "process_refund",       "support",  "process_refund via money return"),
    ("send customer satisfaction form",         "send_satisfaction_survey", "support", "send_satisfaction_survey via form"),

    # ── Health — Trigger synonyms ─────────────────────────────────────────────
    ("patient checked into hospital",           "patient_admitted",     "health",   "patient_admitted via checked in"),
    ("patient was admitted to ward",            "patient_admitted",     "health",   "patient_admitted via ward"),
    ("patient left the hospital",               "patient_discharged",   "health",   "patient_discharged via left"),
    ("patient released from care",              "patient_discharged",   "health",   "patient_discharged via released"),
    ("test results are available",              "lab_result_ready",     "health",   "lab_result_ready via test results"),
    ("blood test came back",                    "lab_result_ready",     "health",   "lab_result_ready via blood test"),
    ("patient skipped appointment",             "appointment_missed",   "health",   "appointment_missed via skipped"),
    ("patient no-show",                         "appointment_missed",   "health",   "appointment_missed via no-show"),
    ("medication not taken on time",            "medication_overdue",   "health",   "medication_overdue via not taken"),
    ("prescription overdue",                    "medication_overdue",   "health",   "medication_overdue via prescription"),
    ("vital signs critical",                    "critical_vitals",      "health",   "critical_vitals via vital signs"),
    ("patient condition deteriorated",          "critical_vitals",      "health",   "critical_vitals via deteriorated"),
    ("insurance claim denied",                  "insurance_denied",     "health",   "insurance_denied via claim denied"),
    ("follow up appointment due",               "followup_due",         "health",   "followup_due via follow up"),

    # ── Health — Action synonyms ──────────────────────────────────────────────
    ("book appointment for patient",            "schedule_appointment",     "health",   "schedule_appointment via book"),
    ("set up doctor visit",                     "schedule_appointment",     "health",   "schedule_appointment via doctor visit"),
    ("alert the medical team",                  "alert_care_team",          "health",   "alert_care_team via medical team"),
    ("notify care staff immediately",           "alert_care_team",          "health",   "alert_care_team via care staff"),
    ("refer patient to specialist",             "escalate_to_specialist",   "health",   "escalate_to_specialist via refer"),
    ("send patient to expert",                  "escalate_to_specialist",   "health",   "escalate_to_specialist via expert"),
    ("notify about test result",                "notify_lab_result",        "health",   "notify_lab_result via test result"),
    ("activate emergency response",             "trigger_emergency_protocol","health",  "trigger_emergency_protocol via emergency"),
    ("send home care instructions",             "send_discharge_instructions","health", "send_discharge_instructions via home care"),
    ("flag as high risk",                       "flag_high_risk_patient",   "health",   "flag_high_risk_patient via high risk"),
    ("send pill reminder to patient",           "send_medication_reminder", "health",   "send_medication_reminder via pill"),
    ("check in on patient wellness",            "send_wellness_check",      "health",   "send_wellness_check via check in"),
    ("request pre-authorization for procedure", "request_insurance_approval","health",  "request_insurance_approval via pre-auth"),
]

@pytest.mark.parametrize(
    "query,expected,domain,note",
    CASES
)
def test_semantic_to_prompt(
    query,
    expected,
    domain,
    note
):
    db = SessionLocal()

    matcher = CatalogMatcher(
        trigger_repository=TriggerDefinitionRepository(db),
        action_repository=ActionDefinitionRepository(db),
        semantic_retriever=SemanticCatalogRetriever(),
    )

    result = matcher.match(db, query)

    all_names = (
        result.trigger_names +
        result.action_names
    )

    assert expected in all_names