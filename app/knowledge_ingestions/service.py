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
        return self._ingest_from_extracted_text(
            document_text=document_text,
            workspace_id=workspace_id,
            source_document=source_document,
            brd_document_id=None,
        )

    def ingest_from_text(
        self,
        document_text: str,
        workspace_id: int = 1,
        source_document: str | None = None,
        brd_document_id: int | None = None,
    ):
        """Ingest pre-extracted document text without running PDF extraction.

        Use this when the caller has already extracted text via
        PdfExtractionPipeline (or any other means) and wants to avoid a
        second, redundant call to MultiModalDocumentExtractor.

        Args:
            document_text:   The full extracted text of the document.
                             Must be a non-empty string.
            workspace_id:    Owning workspace.  Defaults to 1 for
                             backward compatibility with legacy callers.
            source_document: Original filename or document label.
                             Stored verbatim on the WorkflowKnowledge row.
            brd_document_id: Optional FK to the BRDDocument row that produced
                             this text.  When supplied it is written to
                             WorkflowKnowledge.brd_document_id, completing
                             the provenance chain:
                               WorkflowKnowledge → BRDDocument → Workspace → Tenant.

        Returns:
            Persisted WorkflowKnowledge ORM object (same as ingest()).

        Raises:
            WorkflowExtractionError: document_text is empty, or the LLM
                                     extracted zero action references.
            RepositoryError:         Persistence or mapping failed.
        """
        if not document_text or not document_text.strip():
            from app.knowledge_ingestions.exceptions import WorkflowExtractionError
            raise WorkflowExtractionError(
                "document_text is empty — cannot extract workflow knowledge."
            )

        return self._ingest_from_extracted_text(
            document_text=document_text,
            workspace_id=workspace_id,
            source_document=source_document,
            brd_document_id=brd_document_id,
        )

    # ── Shared internal logic ─────────────────────────────────────────────────

    def _ingest_from_extracted_text(
        self,
        document_text: str,
        workspace_id: int,
        source_document: str | None,
        brd_document_id: int | None,
    ):
        """Extract workflow knowledge from text, persist it, and return the row.

        Called by both ingest() and ingest_from_text().  All transaction,
        commit, rollback and error-handling conventions live here exactly once.
        """
        workflow = self.workflow_extractor.extract(document_text)

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

            # Populate provenance link when a BRDDocument id is supplied.
            # The column is nullable so this is a no-op for callers that do
            # not supply it (e.g. the legacy ingest() path).
            if brd_document_id is not None:
                knowledge.brd_document_id = brd_document_id

            self.embedding_mapper.map_actions(workspace_id=workspace_id)
            self.embedding_mapper.map_triggers(workspace_id=workspace_id)
            self.db.commit()
            return knowledge
        except Exception as e:
            self.db.rollback()
            from app.knowledge_ingestions.exceptions import RepositoryError
            raise RepositoryError(f"Failed to persist workflow: {e}") from e
