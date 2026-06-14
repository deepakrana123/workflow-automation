from app.nlp.services.nl_workflow_service import NLPWorkflowService

TEST_CASES = [
    "When payment is due send reminder to customer",
    "When payment is missed escalate case and notify manager",
    "If fraud detected lock account and flag for review",
    "When ticket created assign support agent",
    "If SLA breached send alert and escalate to tier2",
    "When complaint created create support ticket and notify customer",
    "When appointment missed send medication reminder",
    "When critical vitals detected alert care team",
    "When patient discharged send discharge instructions",
]

for case in TEST_CASES:
    print("=" * 80)
    print(case)

    result = NLPWorkflowService().generate(case)

    print(result)