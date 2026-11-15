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
        document_version_id: int | None = None,
        ingestion_attempt: object | None = None,
    ):
        """Ingest pre-extracted document text without running PDF extraction.

        Use this when the caller has already extracted text via
        PdfExtractionPipeline (or any other means) and wants to avoid a
        second, redundant call to MultiModalDocumentExtractor.

        Args:
            document_text:       The full extracted text. Must be non-empty.
            workspace_id:        Owning workspace.
            source_document:     Original filename stored on the knowledge row.
            brd_document_id:     Optional FK to BRDDocument for provenance.
            document_version_id: Optional FK to DocumentVersion. When supplied,
                                 a partial UNIQUE index (added in migration
                                 fix_idempotency_gaps) prevents duplicate rows
                                 for the same version. If the INSERT hits that
                                 constraint (IntegrityError), the existing row
                                 is returned instead.
            ingestion_attempt:   Optional IngestionAttempt ORM row. When supplied,
                                 `extracted_knowledge_id` and `status=COMPLETED`
                                 are written in the SAME commit as WorkflowKnowledge,
                                 making T5 and T6 a single atomic transaction and
                                 eliminating the ghost-knowledge crash window.

        Returns:
            Persisted WorkflowKnowledge ORM object.

        Raises:
            WorkflowExtractionError: document_text is empty or LLM extracted
                                     zero action references.
            RepositoryError:         Persistence or mapping failed.
        """
        if not document_text or not document_text.strip():
            from app.knowledge_ingestions.exceptions import WorkflowExtractionError
            raise WorkflowExtractionError(
                "document_text is empty — cannot extract workflow knowledge."
            )

        # Ghost-knowledge recovery: if a previous crash left a committed
        # WorkflowKnowledge row for this version (T5 done, T6 not done),
        # return it instead of creating a duplicate.
        if document_version_id is not None:
            existing = self._find_existing_knowledge(document_version_id)
            if existing is not None:
                # Link the new attempt to the existing knowledge if supplied,
                # then return — no new extraction needed.
                if ingestion_attempt is not None:
                    self._link_attempt(ingestion_attempt, existing)
                return existing

        return self._ingest_from_extracted_text(
            document_text=document_text,
            workspace_id=workspace_id,
            source_document=source_document,
            brd_document_id=brd_document_id,
            document_version_id=document_version_id,
            ingestion_attempt=ingestion_attempt,
        )

    def _find_existing_knowledge(self, document_version_id: int):
        """Return an existing WorkflowKnowledge row for this version, or None."""
        from app.models.workflow_knowledge import WorkflowKnowledge
        return (
            self.db.query(WorkflowKnowledge)
            .filter(WorkflowKnowledge.document_version_id == document_version_id)
            .first()
        )

    def _link_attempt(self, ingestion_attempt, knowledge) -> None:
        """Link an attempt to recovered existing knowledge and commit."""
        from app.models.ingestion_attempt import AttemptStatus
        from datetime import datetime, timezone
        try:
            ingestion_attempt.extracted_knowledge_id = knowledge.id
            ingestion_attempt.status = AttemptStatus.COMPLETED.value
            ingestion_attempt.completed_at = datetime.now(timezone.utc)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            from app.knowledge_ingestions.exceptions import RepositoryError
            raise RepositoryError(
                f"Failed to link existing knowledge to attempt: {exc}"
            ) from exc

    # ── Shared internal logic ─────────────────────────────────────────────────

    def _ingest_from_extracted_text(
        self,
        document_text: str,
        workspace_id: int,
        source_document: str | None,
        brd_document_id: int | None,
        document_version_id: int | None = None,
        ingestion_attempt: object | None = None,
    ):
        """Extract workflow knowledge from text, persist it, and return the row.

        Called by both ingest() and ingest_from_text(). All transaction,
        commit, rollback and error-handling conventions live here exactly once.

        When ingestion_attempt is supplied, its status and
        extracted_knowledge_id are updated in the SAME commit as
        WorkflowKnowledge — merging T5 and T6 into one atomic transaction.
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
                brd_document_id=brd_document_id,
            )

            # Populate provenance links.
            if brd_document_id is not None:
                knowledge.brd_document_id = brd_document_id
            if document_version_id is not None:
                knowledge.document_version_id = document_version_id

            # Merge T5 + T6: update attempt in the same commit so a crash
            # between the two old commits can no longer produce ghost knowledge.
            if ingestion_attempt is not None:
                from app.models.ingestion_attempt import AttemptStatus
                from datetime import datetime, timezone
                ingestion_attempt.extracted_knowledge_id = knowledge.id
                ingestion_attempt.status = AttemptStatus.COMPLETED.value
                ingestion_attempt.completed_at = datetime.now(timezone.utc)

            self.embedding_mapper.map_actions(workspace_id=workspace_id)
            self.embedding_mapper.map_triggers(workspace_id=workspace_id)
            self.db.commit()
            return knowledge
        except Exception as e:
            self.db.rollback()
            from app.knowledge_ingestions.exceptions import RepositoryError
            raise RepositoryError(f"Failed to persist workflow: {e}") from e
