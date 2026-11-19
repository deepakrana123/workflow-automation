"""
app/semantic/embedding_consistency.py

Embedding consistency checks and recovery for Phase 6 hardening.

Responsibilities:
1. Validate embedding existence and dimensions during retrieval
2. Detect NULL embeddings and log visibility events
3. Enforce idempotency during backfill (no partial updates)
4. Handle stale embeddings after model version changes
5. Track embedding generation metadata reliably

Design:
- Detection-only — no automatic regeneration
- Fail loudly when embeddings missing/stale at retrieval time
- Backfill wrapped in transaction with rollback on error
- Dimension validation on insertion
"""

from app.core.logger import logger
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func
from app.models.action_definitions import ActionDefinition
from app.models.trigger_definitions import TriggerDefinition
from app.models.workflow_business_rule import WorkflowBusinessRule
from app.models.workflow_knowledge import WorkflowKnowledge


CONFIGURED_EMBEDDING_DIM = 384
CONFIGURED_MODEL_NAME = "BAAI/bge-small-en-v1.5"
CONFIGURED_MODEL_VERSION = "1.5"


class EmbeddingConsistencyCheck:
    """Validates embedding consistency for retrieval safety."""

    @staticmethod
    def validate_embedding_dimension(embedding: list[float]) -> None:
        """
        Enforce dimension consistency.

        Raises ValueError if embedding does not match configured dimension.
        Called before inserting any new embedding.
        """
        if embedding is None:
            raise ValueError("Embedding cannot be None")
        
        actual_dim = len(embedding)
        if actual_dim != CONFIGURED_EMBEDDING_DIM:
            raise ValueError(
                f"Embedding dimension mismatch: got {actual_dim}, "
                f"expected {CONFIGURED_EMBEDDING_DIM}"
            )

    @staticmethod
    def validate_entity_embeddings(
        db: Session,
        entity_type: str,
        workspace_id: int | None = None,
    ) -> dict[str, int]:
        """
        Check for NULL embeddings in a given entity type.

        Returns dict with counts:
            - total: total records in entity
            - with_embedding: records with non-NULL embedding
            - without_embedding: records with NULL embedding
            - missing_metadata: records with embedding but missing model metadata

        Logs warnings if any NULL embeddings found.
        """
        stats = {
            "total": 0,
            "with_embedding": 0,
            "without_embedding": 0,
            "missing_metadata": 0,
        }

        if entity_type == "action":
            model_class = ActionDefinition
        elif entity_type == "trigger":
            model_class = TriggerDefinition
        elif entity_type == "business_rule":
            model_class = WorkflowBusinessRule
        else:
            raise ValueError(f"Unknown entity_type: {entity_type}")

        # Count totals
        q_total = select(func.count(model_class.id))
        if entity_type == "business_rule" and workspace_id is not None:
            q_total = q_total.join(WorkflowKnowledge).filter(
                WorkflowKnowledge.workspace_id == workspace_id
            )
        stats["total"] = db.scalar(q_total)

        # Count with embeddings
        q_with = select(func.count(model_class.id)).filter(
            model_class.embedding.isnot(None)
        )
        if entity_type == "business_rule" and workspace_id is not None:
            q_with = q_with.join(WorkflowKnowledge).filter(
                WorkflowKnowledge.workspace_id == workspace_id
            )
        stats["with_embedding"] = db.scalar(q_with)

        # Count without embeddings
        q_without = select(func.count(model_class.id)).filter(
            model_class.embedding.is_(None)
        )
        if entity_type == "business_rule" and workspace_id is not None:
            q_without = q_without.join(WorkflowKnowledge).filter(
                WorkflowKnowledge.workspace_id == workspace_id
            )
        stats["without_embedding"] = db.scalar(q_without)

        # Count missing metadata
        q_missing_meta = select(func.count(model_class.id)).filter(
            and_(
                model_class.embedding.isnot(None),
                (model_class.embedding_model_name.is_(None)) | (model_class.embedding_model_version.is_(None)),
            )
        )
        if entity_type == "business_rule" and workspace_id is not None:
            q_missing_meta = q_missing_meta.join(WorkflowKnowledge).filter(
                WorkflowKnowledge.workspace_id == workspace_id
            )
        stats["missing_metadata"] = db.scalar(q_missing_meta)

        # Log warnings
        if stats["without_embedding"] > 0:
            logger.warning(
                "embedding_consistency_null_embeddings",
                extra={
                    "extra_data": {
                        "entity_type": entity_type,
                        "workspace_id": workspace_id,
                        "count": stats["without_embedding"],
                    }
                },
            )

        if stats["missing_metadata"] > 0:
            logger.warning(
                "embedding_consistency_missing_metadata",
                extra={
                    "extra_data": {
                        "entity_type": entity_type,
                        "workspace_id": workspace_id,
                        "count": stats["missing_metadata"],
                    }
                },
            )

        return stats


class BackfillIdempotency:
    """Ensures backfill operations are idempotent and transactional."""

    @staticmethod
    def backfill_batch_transactional(
        db: Session,
        records: list[tuple[int, object]],
        embeddings: list[list[float]],
        model_name: str,
        model_version: str,
        model_class: type,
    ) -> tuple[int, int, list[int]]:
        """
        Atomically update a batch of embeddings or rollback entirely.

        All-or-nothing semantics: either all embeddings in this batch commit,
        or none do. Partial batches are rejected.

        Args:
            db: SQLAlchemy session
            records: List of (record_id, record_object) tuples
            embeddings: List of embedding vectors (same order as records)
            model_name: Embedding model name (e.g., "BAAI/bge-small-en-v1.5")
            model_version: Embedding model version (e.g., "1.5")
            model_class: The model class (ActionDefinition, etc.)

        Returns:
            (updated_count, failed_count, failed_record_ids)

        Raises:
            ValueError: If embedding dimension mismatch
            Exception: If transaction rollback fails
        """
        from datetime import datetime, timezone

        if len(records) != len(embeddings):
            raise ValueError(
                f"Records and embeddings length mismatch: "
                f"{len(records)} vs {len(embeddings)}"
            )

        updated_count = 0
        failed_count = 0
        failed_ids = []
        generated_at = datetime.now(timezone.utc)

        try:
            for (record_id, record), embedding in zip(records, embeddings):
                try:
                    # Validate dimension before updating
                    EmbeddingConsistencyCheck.validate_embedding_dimension(embedding)

                    # Update in-memory record
                    record.embedding = embedding
                    record.embedding_model_name = model_name
                    record.embedding_model_version = model_version
                    record.embedding_generated_at = generated_at
                    updated_count += 1
                except ValueError as e:
                    logger.error(
                        "embedding_consistency_dimension_error",
                        extra={
                            "extra_data": {
                                "record_id": record_id,
                                "model_class": model_class.__name__,
                                "error": str(e),
                            }
                        },
                    )
                    failed_count += 1
                    failed_ids.append(record_id)

            # If any record failed validation, rollback entire batch
            if failed_count > 0:
                logger.warning(
                    "embedding_consistency_batch_rollback",
                    extra={
                        "extra_data": {
                            "model_class": model_class.__name__,
                            "total": len(records),
                            "failed": failed_count,
                            "failed_ids": failed_ids[:10],  # Log first 10
                        }
                    },
                )
                db.rollback()
                return 0, failed_count, failed_ids

            # All records validated; commit transaction
            db.commit()
            logger.info(
                "embedding_consistency_batch_committed",
                extra={
                    "extra_data": {
                        "model_class": model_class.__name__,
                        "count": updated_count,
                    }
                },
            )
            return updated_count, 0, []

        except Exception as e:
            logger.exception(
                "embedding_consistency_transaction_error",
                extra={
                    "extra_data": {
                        "model_class": model_class.__name__,
                        "batch_size": len(records),
                    }
                },
            )
            db.rollback()
            raise


class StaleEmbeddingDetection:
    """Detect and report on stale embeddings (model version mismatches)."""

    @staticmethod
    def find_stale_embeddings(
        db: Session,
        entity_type: str,
        workspace_id: int | None = None,
        current_model_name: str = CONFIGURED_MODEL_NAME,
        current_model_version: str = CONFIGURED_MODEL_VERSION,
    ) -> dict[str, int]:
        """
        Find stale embeddings for a given entity type.

        Returns dict with counts:
            - stale_model_version: embeddings from different model version
            - missing_model_metadata: embeddings missing model name/version
            - total_stale: sum of above

        Logs warning if any stale embeddings found.
        """
        stats = {
            "stale_model_version": 0,
            "missing_model_metadata": 0,
            "total_stale": 0,
        }

        if entity_type == "action":
            model_class = ActionDefinition
        elif entity_type == "trigger":
            model_class = TriggerDefinition
        elif entity_type == "business_rule":
            model_class = WorkflowBusinessRule
        else:
            raise ValueError(f"Unknown entity_type: {entity_type}")

        # Find stale versions
        q_stale = select(func.count(model_class.id)).filter(
            and_(
                model_class.embedding.isnot(None),
                (model_class.embedding_model_version != current_model_version)
                | (model_class.embedding_model_name != current_model_name),
            )
        )
        if entity_type == "business_rule" and workspace_id is not None:
            q_stale = q_stale.join(WorkflowKnowledge).filter(
                WorkflowKnowledge.workspace_id == workspace_id
            )
        stats["stale_model_version"] = db.scalar(q_stale)

        # Find missing metadata
        q_missing = select(func.count(model_class.id)).filter(
            and_(
                model_class.embedding.isnot(None),
                (model_class.embedding_model_name.is_(None))
                | (model_class.embedding_model_version.is_(None)),
            )
        )
        if entity_type == "business_rule" and workspace_id is not None:
            q_missing = q_missing.join(WorkflowKnowledge).filter(
                WorkflowKnowledge.workspace_id == workspace_id
            )
        stats["missing_model_metadata"] = db.scalar(q_missing)

        stats["total_stale"] = (
            stats["stale_model_version"] + stats["missing_model_metadata"]
        )

        if stats["total_stale"] > 0:
            logger.warning(
                "embedding_consistency_stale_detected",
                extra={
                    "extra_data": {
                        "entity_type": entity_type,
                        "workspace_id": workspace_id,
                        "stale_version": stats["stale_model_version"],
                        "missing_metadata": stats["missing_model_metadata"],
                    }
                },
            )

        return stats
