from app.db.session import SessionLocal
from app.semantic.semantic_catalog_retriever import SemanticCatalogRetriever

SEMANTIC_CASES = [

    # Trigger synonyms

    ("customer forgot appointment",
     "appointment_missed"),

    ("user did not attend appointment",
     "appointment_missed"),

    ("loan application arrived",
     "loan_requested"),

    ("new borrowing request submitted",
     "loan_requested"),

    ("payment was not received",
     "payment_missed"),

    ("invoice still unpaid",
     "payment_missed"),

    ("customer wants money back",
     "refund_requested"),

    ("refund needed",
     "refund_requested"),

    ("fraudulent transaction detected",
     "fraud_detected"),

    ("suspicious account activity",
     "fraud_detected"),

    # Actions

    ("tell supervisor immediately",
     "notify_manager"),

    ("inform the manager",
     "notify_manager"),

    ("raise the case to higher level",
     "escalate_case"),

    ("send warning to customer",
     "send_reminder"),

    ("freeze customer account",
     "lock_account"),

    ("mark for investigation",
     "flag_for_review"),

    ("create audit trail",
     "create_audit_record"),

    ("assign employee to ticket",
     "assign_support_agent"),

    ("solve support issue",
     "resolve_ticket"),

    ("close support case",
     "close_case"),
]

db =SessionLocal()
retriever=SemanticCatalogRetriever()



for query, expected in SEMANTIC_CASES:

    triggers, actions = retriever.retrieve(
        db,
        query
    )

    names = [
        x.name for x in triggers
    ] + [
        x.name for x in actions
    ]

    if expected in names:
        print(f"PASS {query}")
    else:
        print(f"FAIL {query}")