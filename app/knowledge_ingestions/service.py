from pathlib import Path
from sqlalchemy.orm import Session

from app.knowledge_ingestions.multimodal_extractor import MultiModalDocumentExtractor
from app.knowledge_ingestions.worfklow_extractors import WorkflowExtractor
from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from app.knowledge_ingestions.embedding_mapper import EmbeddingMapper
from app.retrieval.vector_retriever import VectorRetriever
from app.retrieval.keyword_retriever import KeywordRetriever
from app.retrieval.postgress_retriever import PostgressRetriever
from app.retrieval.reciprocal_rank_fusion import ReciprocalRankFusion
from app.retrieval.cross_encoder import CrossEncoderReRanker
from app.retrieval.decision_engine import MappingDecisionEngine
from app.retrieval.confidene_estimator import ConfidenceEstimator
from app.retrieval.thresholds import RetrievalThresholds
from app.retrieval.unknown_detector import UnkownDetetor
from app.retrieval.pipeline import RetrievalPipeline


def _build_pipeline(repository: WorkflowRepository) -> RetrievalPipeline:
    return RetrievalPipeline(
        vector_retriever  = VectorRetriever(repository),
        keyword_retriever = KeywordRetriever(repository),
        postgres_retriever = PostgressRetriever(repository),
        rrf               = ReciprocalRankFusion(),
        cross_encoder     = CrossEncoderReRanker(),
        decision_engine   = MappingDecisionEngine(
            confidene_estimator = ConfidenceEstimator(),
            thresholds          = RetrievalThresholds(),
            unknown_detector    = UnkownDetetor(),
        ),
    )


class KnowledgeIngestionService:

    def __init__(
        self,
        db: Session,
        document_extractor: MultiModalDocumentExtractor | None = None,
        workflow_extractor: WorkflowExtractor | None = None,
        repository: WorkflowRepository | None = None,
        embedding_mapper: EmbeddingMapper | None = None,
    ):
        self.db                  = db
        self.repository         = repository or WorkflowRepository(db)
        # MultiModalDocumentExtractor replaces the old DocumentExtractor.
        # It resolves providers from env vars (VISION_PROVIDER, TEXT_PROVIDER)
        # at construction time. Plain-text-only PDFs take the fast pypdf path
        # automatically — no vision API calls are made unless needed.
        self.document_extractor = document_extractor or MultiModalDocumentExtractor()
        self.workflow_extractor  = workflow_extractor or WorkflowExtractor()
        if embedding_mapper is not None:
            self.embedding_mapper = embedding_mapper
        else:
            pipeline = _build_pipeline(self.repository)
            self.embedding_mapper = EmbeddingMapper(self.repository, pipeline)

    def ingest(
        self,
        file_path: Path,
        workspace_id: int = 1,
        source_document: str | None = None,
    ):
        document_text = self.document_extractor.extract(file_path)
        workflow      = self.workflow_extractor.extract(document_text)

        if not workflow.action_references:
            from app.knowledge_ingestions.exceptions import WorkflowExtractionError
            raise WorkflowExtractionError(
                f"No actions could be extracted from this document. "
                f"Workflow: '{workflow.workflow_name}'. "
                f"Summary: {workflow.summary}"
            )

        try:
            knowledge = self.repository.save(
                workflow,
                workspace_id=workspace_id,
                source_document=source_document,
            )
            self.embedding_mapper.map_actions()
            self.embedding_mapper.map_triggers()
            self.db.commit()
            return knowledge
        except Exception as e:
            self.db.rollback()
            from app.knowledge_ingestions.exceptions import RepositoryError
            raise RepositoryError(f"Failed to persist workflow: {e}") from e
