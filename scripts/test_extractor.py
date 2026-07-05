

# from pathlib import Path

from app.db.session import SessionLocal
# from app.knowledge_ingestions.extractor import DocumentExtractor
# from app.knowledge_ingestions.worfklow_extractors import WorkflowExtractor
from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from app.knowledge_ingestions.embedding_mapper import EmbeddingMapper
db = SessionLocal()

# document_extractor = DocumentExtractor()
# workflow_extractor = WorkflowExtractor()
# repository = WorkflowRepository(db)

# pdfs = [
#     Path(r"C:\Users\Devendra\Downloads\jkl.pdf"),
#     # Path(r"C:\Users\Devendra\Downloads\bcd.pdf"),
#     # Path(r"C:\Users\Devendra\Downloads\cde.pdf"),
#     # Path(r"C:\Users\Devendra\Downloads\def.pdf"),
#     # Path(r"C:\Users\Devendra\Downloads\efg.pdf")
#     # Path(r"C:\Users\Devendra\Downloads\fgh.pdf")
#     # Path(r"C:\Users\Devendra\Downloads\ghi.pdf"),
# ]

# for pdf in pdfs:
#     print("=" * 80)
#     print(pdf.name)

#     try:
#         text = document_extractor.extract(pdf)
       
#         workflow = workflow_extractor.extract(text)
#         print(workflow)
#         knowledge = repository.save(workflow)

#         print(f"✅ Saved workflow {knowledge.id}")

#     except Exception as e:
#         print(f"❌ {pdf.name}")
#         print(e)
repository = WorkflowRepository(db)
embedding=EmbeddingMapper(repository)
try:
    embedding.map_triggers()
except Exception as e:
    print(e)