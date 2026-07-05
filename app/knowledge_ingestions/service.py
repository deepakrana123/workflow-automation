from pathlib import Path
from app.knowledge_ingestions.extractor import DocumentExtractor
from app.knowledge_ingestions.worfklow_extractors import WorkflowExtractor
from app.knowledge_ingestions.workflow_mapper import WorkflowMapper
from app.knowledge_ingestions.workflow_repository import WorkflowRepository


class KnowledgeIngestionService:
    def __init__(self):
        self.document_extractor = DocumentExtractor()
        self.workflow_extractor = WorkflowExtractor()
        self.mapper = WorkflowMapper()
        self.repository = WorkflowRepository()

    def ingest(self, file_path: Path):
        document_text = self.document_extractor.extract(file_path)
        workflow = self.workflow_extractor.extract(document_text)
        payload = self.mapper.to_dict(workflow)
        self.repository.save(payload)
        return workflow
