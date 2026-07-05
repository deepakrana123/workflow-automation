from pathlib import Path
from sqlalchemy.orm import Session

from app.knowledge_ingestions.extractor import DocumentExtractor
from app.knowledge_ingestions.worfklow_extractors import WorkflowExtractor
from app.knowledge_ingestions.workflow_mapper import WorkflowMapper
from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from app.knowledge_ingestions.embedding_mapper import EmbeddingMapper


class KnowledgeIngestionService:

    def __init__(self, db: Session):
        self.document_extractor = DocumentExtractor()
        self.workflow_extractor = WorkflowExtractor()
        self.mapper = WorkflowMapper()
        self.repository = WorkflowRepository(db)
        self.embedding_mapper = EmbeddingMapper(self.repository)

    def ingest(self, file_path: Path):
        document_text = self.document_extractor.extract(file_path)
        workflow = self.workflow_extractor.extract(document_text)
        knowledge = self.repository.save(workflow)
        self.embedding_mapper.map_actions()
        self.embedding_mapper.map_triggers()
        return knowledge
