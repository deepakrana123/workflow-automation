# # from pathlib import Path

# # from app.knowledge_ingestions.extractor import DocumentExtractor

# # extractor = DocumentExtractor()

# # for pdf in [
# #     r"C:\Users\Devendra\Downloads\sample_text.pdf",
# #     r"C:\Users\Devendra\Downloads\sample_scanned.pdf",
# # ]:
# #     print("=" * 80)
# #     print(pdf)

# #     text = extractor.extract(Path(pdf))

# #     print(text[:500])


# from app.db.session import SessionLocal

# from app.knowledge_ingestions.schemas import (
#     WorkflowExtraction,
#     TriggerExtraction,
#     ActionReference,
#     BussinessRule,
#     Actor,
#     ExternalSystem,
# )

# from app.knowledge_ingestions.workflow_repository import WorkflowRepository

# db = SessionLocal()

# workflow = WorkflowExtraction(
#     workflow_name="Loan Approval",
#     summary="Loan approval workflow",
#     triggers=[
#         TriggerExtraction(
#             name="Loan Application Submitted",
#             description="Customer submits loan application",
#         )
#     ],
#     action_references=[
#         ActionReference(
#             name="Validate KYC",
#             description="Verify customer identity",
#         ),
#         ActionReference(
#             name="Credit Check",
#             description="Fetch customer credit score",
#         ),
#     ],
#     business_rules=[BussinessRule(rule="Reject if mandatory documents are missing.")],
#     actors=[
#         Actor(
#             name="Loan Officer",
#             role="Approves loan",
#         )
#     ],
#     external_systems=[
#         ExternalSystem(
#             name="Experian",
#             description="Credit bureau",
#         )
#     ],
# )

# repo = WorkflowRepository(db)

# knowledge = repo.save(workflow)

# print(f"Workflow ID: {knowledge.id}")


from pathlib import Path

from app.db.session import SessionLocal
from app.knowledge_ingestions.extractor import DocumentExtractor
from app.knowledge_ingestions.worfklow_extractors import WorkflowExtractor
from app.knowledge_ingestions.workflow_repository import WorkflowRepository

db = SessionLocal()

document_extractor = DocumentExtractor()
workflow_extractor = WorkflowExtractor()
repository = WorkflowRepository(db)

pdfs = [
    Path(r"C:\Users\Devendra\Downloads\jkl.pdf"),
    # Path(r"C:\Users\Devendra\Downloads\bcd.pdf"),
    # Path(r"C:\Users\Devendra\Downloads\cde.pdf"),
    # Path(r"C:\Users\Devendra\Downloads\def.pdf"),
    # Path(r"C:\Users\Devendra\Downloads\efg.pdf")
    # Path(r"C:\Users\Devendra\Downloads\fgh.pdf")
    # Path(r"C:\Users\Devendra\Downloads\ghi.pdf"),
]

for pdf in pdfs:
    print("=" * 80)
    print(pdf.name)

    try:
        text = document_extractor.extract(pdf)
       
        workflow = workflow_extractor.extract(text)
        print(workflow)
        knowledge = repository.save(workflow)

        print(f"✅ Saved workflow {knowledge.id}")

    except Exception as e:
        print(f"❌ {pdf.name}")
        print(e)
