
from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterator

from sentence_transformers import SentenceTransformer
from sqlalchemy import select, and_

from app.db.session import SessionLocal
from app.models.action_definitions import ActionDefinition
from app.models.trigger_definitions import TriggerDefinition
from app.models.workflow_business_rule import WorkflowBusinessRule
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workspace import Workspace
from app.models.tenant import Tenant


MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSION = 384
DEFAULT_DB_BATCH_SIZE = 256
DEFAULT_INFERENCE_BATCH_SIZE = 32

logger = logging.getLogger("embedding_backfill")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


@dataclass
class BackfillStats:
    total: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    processed_batches: int = 0
    failed_record_ids: list[int] = field(default_factory=list)
    
    def add_failure(self, record_id: int) -> None:
        """Track failed record ID for potential retry reporting."""
        self.failed_record_ids.append(record_id)


def normalize_aliases(aliases: Any) -> list[str]:
    if aliases is None:
        return []

    if not isinstance(aliases, list):
        raise ValueError(
            f"aliases must be a list, got {type(aliases).__name__}"
        )

    normalized = []

    for alias in aliases:
        if alias is None:
            continue

        alias_text = str(alias).strip()

        if alias_text:
            normalized.append(alias_text)

    return normalized


def build_trigger_text(trigger: TriggerDefinition) -> str:
    """Build the text embedded for a TriggerDefinition.

    Format must match what EmbeddingMapper._build_embedding_text produces so
    that BRD queries and catalog entries live in the same embedding space.
    """
    aliases = normalize_aliases(trigger.aliases)
    parts = [
        trigger.name.replace("_", " ") if trigger.name else "",
        trigger.display_name or "",
        " ".join(aliases),
        trigger.description or "",
    ]
    return " ".join(p for p in parts if p).strip()


def build_action_text(action: ActionDefinition) -> str:
    """Build the text embedded for an ActionDefinition.

    Format must match what EmbeddingMapper._build_embedding_text produces so
    that BRD queries and catalog entries live in the same embedding space.
    """
    aliases = normalize_aliases(action.aliases)
    parts = [
        action.name.replace("_", " ") if action.name else "",
        action.display_name or "",
        " ".join(aliases),
        action.description or "",
    ]
    return " ".join(p for p in parts if p).strip()


def build_business_rule_text(rule: WorkflowBusinessRule) -> str:
    parts = [
        f"Rule: {rule.rule or ''}",
        f"Condition: {rule.condition or ''}",
        f"Outcome: {rule.outcome or ''}",
        f"Responsible Role: {rule.responsible_role or ''}",
        f"Threshold: {rule.threshold or ''}",
    ]

    return "\n".join(
        part
        for part in parts
        if part.split(":", 1)[-1].strip()
    )


def validate_embedding(embedding: list[float]) -> None:
    actual_dimension = len(embedding)

    if actual_dimension != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Unexpected embedding dimension: "
            f"{actual_dimension}. "
            f"Expected: {EMBEDDING_DIMENSION}"
        )


# ── Batch Processing & Resumability ──────────────────────────────────────────


def fetch_pending_record_batch(
    session: Any,
    model_class: type,
    db_batch_size: int,
    force: bool = False,
    resume_from: int | None = None,
    workspace_id: int | None = None,
) -> list[tuple[int, Any]]:
    """
    Fetch a batch of records that need embeddings using keyset pagination.
    
    Stable keyset pagination avoids OFFSET performance issues with large tables.
    Uses primary key as the stable watermark.
    
    Returns list of (id, record) tuples to maintain identity across session boundaries.
    """
    # Build base query
    filters = []
    
    if model_class == WorkflowBusinessRule and workspace_id is not None:
        # Workspace-scoped business rule query
        q = select(model_class).join(WorkflowKnowledge).filter(
            WorkflowKnowledge.workspace_id == workspace_id
        )
    else:
        q = select(model_class)
    
    # Filter by embedding status (unless force=True)
    if not force:
        q = q.filter(model_class.embedding.is_(None))
    
    # Keyset pagination: only fetch records with id > resume_from
    if resume_from is not None:
        q = q.filter(model_class.id > resume_from)
    
    # Order by id for stable iteration
    q = q.order_by(model_class.id).limit(db_batch_size)
    
    # Fetch without loading into memory; return (id, record) tuples
    records = session.scalars(q).all()
    return [(r.id, r) for r in records]


def process_batch_inference(
    batch_records: list[tuple[int, Any]],
    model: SentenceTransformer,
    text_builder: callable,
    inference_batch_size: int,
) -> dict[int, tuple[list[float], str] | Exception]:
    """
    Run inference on a batch of records.
    
    Inference runs in separate batches (size: inference_batch_size) to control
    GPU/memory usage independently of database batch size.
    
    Returns dict mapping record_id -> (embedding_vector, None) or record_id -> Exception.
    Exceptions are captured per-record to allow partial batch success.
    """
    results: dict[int, tuple[list[float], str] | Exception] = {}
    
    # Collect text and track IDs
    pending: list[tuple[int, Any]] = []
    pending_texts: list[str] = []
    
    for record_id, record in batch_records:
        try:
            text = text_builder(record).strip()
            if not text:
                logger.warning("Record %s: empty embedding text, skipping", record_id)
                results[record_id] = None  # Will be counted as skipped
                continue
            pending.append((record_id, record))
            pending_texts.append(text)
        except Exception as e:
            logger.exception("Record %s: failed to build text", record_id)
            results[record_id] = e
    
    if not pending_texts:
        return results
    
    # Run inference with configurable batch size
    try:
        embeddings = model.encode(
            pending_texts,
            batch_size=inference_batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
    except Exception as e:
        logger.exception("Inference failed for batch of %s records", len(pending_texts))
        for record_id, _ in pending:
            results[record_id] = e
        return results
    
    # Validate and store embeddings
    for (record_id, record), embedding in zip(pending, embeddings):
        try:
            vector = embedding.tolist()
            validate_embedding(vector)
            results[record_id] = (vector, None)
        except Exception as e:
            logger.exception("Record %s: validation failed", record_id)
            results[record_id] = e
    
    return results


def commit_batch_updates(
    session: Any,
    batch_records: list[tuple[int, Any]],
    inference_results: dict[int, tuple[list[float], str] | Exception | None],
    model_name: str | None,
    model_version: str | None,
) -> tuple[int, int, list[int]]:
    """
    Commit updates for a single batch.
    
    Each batch commits independently. If commit fails, previously committed batches
    remain in the database.
    
    Returns (updated_count, failed_count, failed_record_ids).
    """
    updated = 0
    failed = 0
    failed_ids: list[int] = []
    generated_at = datetime.now(timezone.utc)
    
    for record_id, record in batch_records:
        result = inference_results.get(record_id)
        
        if result is None:
            # Skipped (empty text)
            continue
        
        if isinstance(result, Exception):
            failed += 1
            failed_ids.append(record_id)
            logger.debug("Record %s: inference failed (%s)", record_id, type(result).__name__)
            continue
        
        vector, _ = result
        try:
            # Update record with embedding and metadata
            record.embedding = vector
            record.embedding_model_name = model_name
            record.embedding_model_version = model_version
            record.embedding_generated_at = generated_at
            updated += 1
        except Exception as e:
            failed += 1
            failed_ids.append(record_id)
            logger.exception("Record %s: failed to update record", record_id)
    
    # Commit this batch independently
    try:
        session.commit()
        logger.info(
            "Batch commit: updated=%s failed=%s",
            updated,
            failed,
        )
    except Exception as e:
        session.rollback()
        logger.exception("Batch commit failed, rolling back")
        raise
    
    return updated, failed, failed_ids
    logger.info("Loading embedding model: %s", MODEL_NAME)

    model = SentenceTransformer(MODEL_NAME)

    actual_dimension = model.get_embedding_dimension()

    logger.info(
        "Embedding model loaded: %s | Actual dimension: %s",
        MODEL_NAME,
        actual_dimension,
    )

    if actual_dimension != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Model dimension mismatch: "
            f"model={actual_dimension}, "
            f"expected={EMBEDDING_DIMENSION}"
        )

    return model


def backfill_business_rules(
    session: Any,
    model: SentenceTransformer,
    force: bool = False,
    workspace_id: int | None = None,
    tenant_id: int | None = None,
    model_name: str | None = None,
    model_version: str | None = None,
    db_batch_size: int = DEFAULT_DB_BATCH_SIZE,
    inference_batch_size: int = DEFAULT_INFERENCE_BATCH_SIZE,
    resume_from: int | None = None,
) -> BackfillStats:
    """
    Backfill embeddings for WorkflowBusinessRule records using batch processing.
    
    Processes records in database batches, runs inference in separate batches,
    and commits each batch independently for resumability and fault tolerance.
    
    Args:
        session: SQLAlchemy session
        model: Embedding model
        force: If True, regenerate embeddings for all rows
        workspace_id: Optional workspace_id to scope backfill to one workspace
        tenant_id: Optional tenant_id for validation when workspace_id is supplied
        model_name: Embedding model identifier
        model_version: Model version string
        db_batch_size: Records fetched per database batch
        inference_batch_size: Records processed per inference batch
        resume_from: Primary key watermark to resume from (records with id > resume_from)
        
    Raises:
        ValueError: If tenant_id is supplied but workspace doesn't belong to it
    """
    stats = BackfillStats()

    # ── Validate workspace if scoped ──────────────────────────────────────────
    if workspace_id is not None:
        if tenant_id is not None:
            workspace = session.query(Workspace).filter(
                Workspace.id == workspace_id,
                Workspace.tenant_id == tenant_id,
                Workspace.active.is_(True),
            ).first()
            
            if workspace is None:
                raise ValueError(
                    f"Workspace {workspace_id} not found, inactive, or does not "
                    f"belong to tenant {tenant_id}."
                )
            logger.info(
                "Workspace validation passed: workspace_id=%s tenant_id=%s",
                workspace_id,
                tenant_id,
            )
        else:
            workspace = session.query(Workspace).filter(
                Workspace.id == workspace_id,
                Workspace.active.is_(True),
            ).first()
            
            if workspace is None:
                raise ValueError(
                    f"Workspace {workspace_id} not found or is inactive."
                )
            logger.info(
                "Workspace validation passed: workspace_id=%s",
                workspace_id,
            )

    # ── Batch processing loop ────────────────────────────────────────────────
    current_watermark = resume_from
    
    while True:
        try:
            # Fetch a database batch using keyset pagination
            batch_records = fetch_pending_record_batch(
                session,
                WorkflowBusinessRule,
                db_batch_size,
                force=force,
                resume_from=current_watermark,
                workspace_id=workspace_id,
            )
            
            if not batch_records:
                # No more records to process
                break
            
            logger.info(
                "Processing batch of %s records (starting from id > %s)",
                len(batch_records),
                current_watermark or "None",
            )
            
            # Run inference on this batch
            inference_results = process_batch_inference(
                batch_records,
                model,
                build_business_rule_text,
                inference_batch_size,
            )
            
            # Count skipped before commit attempt
            for record_id, result in inference_results.items():
                if result is None:
                    stats.skipped += 1
            
            # Commit this batch independently
            updated, failed, failed_ids = commit_batch_updates(
                session,
                batch_records,
                inference_results,
                model_name,
                model_version,
            )
            
            stats.updated += updated
            stats.failed += failed
            stats.failed_record_ids.extend(failed_ids)
            stats.processed_batches += 1
            
            # Update watermark for resumability
            last_record_id = batch_records[-1][0]
            current_watermark = last_record_id
            
        except Exception as e:
            logger.exception("Batch processing failed, stopping")
            # Don't rollback—previous batches already committed
            raise

    stats.total = stats.updated + stats.skipped + stats.failed
    return stats


def backfill_triggers(
    session: Any,
    model: SentenceTransformer,
    force: bool = False,
    model_name: str | None = None,
    model_version: str | None = None,
    db_batch_size: int = DEFAULT_DB_BATCH_SIZE,
    inference_batch_size: int = DEFAULT_INFERENCE_BATCH_SIZE,
    resume_from: int | None = None,
) -> BackfillStats:
    """Backfill embeddings for TriggerDefinition records using batch processing."""
    stats = BackfillStats()
    current_watermark = resume_from
    
    while True:
        try:
            batch_records = fetch_pending_record_batch(
                session,
                TriggerDefinition,
                db_batch_size,
                force=force,
                resume_from=current_watermark,
            )
            
            if not batch_records:
                break
            
            logger.info(
                "Processing trigger batch of %s records (starting from id > %s)",
                len(batch_records),
                current_watermark or "None",
            )
            
            inference_results = process_batch_inference(
                batch_records,
                model,
                build_trigger_text,
                inference_batch_size,
            )
            
            for record_id, result in inference_results.items():
                if result is None:
                    stats.skipped += 1
            
            updated, failed, failed_ids = commit_batch_updates(
                session,
                batch_records,
                inference_results,
                model_name,
                model_version,
            )
            
            stats.updated += updated
            stats.failed += failed
            stats.failed_record_ids.extend(failed_ids)
            stats.processed_batches += 1
            
            last_record_id = batch_records[-1][0]
            current_watermark = last_record_id
            
        except Exception as e:
            logger.exception("Trigger batch processing failed, stopping")
            raise
    
    stats.total = stats.updated + stats.skipped + stats.failed
    return stats


def backfill_actions(
    session: Any,
    model: SentenceTransformer,
    force: bool = False,
    model_name: str | None = None,
    model_version: str | None = None,
    db_batch_size: int = DEFAULT_DB_BATCH_SIZE,
    inference_batch_size: int = DEFAULT_INFERENCE_BATCH_SIZE,
    resume_from: int | None = None,
) -> BackfillStats:
    """Backfill embeddings for ActionDefinition records using batch processing."""
    stats = BackfillStats()
    current_watermark = resume_from
    
    while True:
        try:
            batch_records = fetch_pending_record_batch(
                session,
                ActionDefinition,
                db_batch_size,
                force=force,
                resume_from=current_watermark,
            )
            
            if not batch_records:
                break
            
            logger.info(
                "Processing action batch of %s records (starting from id > %s)",
                len(batch_records),
                current_watermark or "None",
            )
            
            inference_results = process_batch_inference(
                batch_records,
                model,
                build_action_text,
                inference_batch_size,
            )
            
            for record_id, result in inference_results.items():
                if result is None:
                    stats.skipped += 1
            
            updated, failed, failed_ids = commit_batch_updates(
                session,
                batch_records,
                inference_results,
                model_name,
                model_version,
            )
            
            stats.updated += updated
            stats.failed += failed
            stats.failed_record_ids.extend(failed_ids)
            stats.processed_batches += 1
            
            last_record_id = batch_records[-1][0]
            current_watermark = last_record_id
            
        except Exception as e:
            logger.exception("Action batch processing failed, stopping")
            raise
    
    stats.total = stats.updated + stats.skipped + stats.failed
    return stats


def log_stats(
    name: str,
    stats: BackfillStats,
) -> None:
    logger.info(
        "%s backfill: total=%s updated=%s skipped=%s failed=%s",
        name,
        stats.total,
        stats.updated,
        stats.skipped,
        stats.failed,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill catalog and rule embeddings")
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Regenerate embeddings for ALL rows (default: skip existing embeddings)",
    )
    parser.add_argument(
        "--workspace-id",
        type=int,
        default=None,
        help="Scope business rule backfill to a specific workspace (catalog backfill is always global)",
    )
    parser.add_argument(
        "--tenant-id",
        type=int,
        default=None,
        help="Validate workspace belongs to this tenant (requires --workspace-id)",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default=MODEL_NAME,
        help=f"Embedding model identifier (default: {MODEL_NAME})",
    )
    parser.add_argument(
        "--model-version",
        type=str,
        default="1.5",
        help="Embedding model version (default: 1.5)",
    )
    parser.add_argument(
        "--db-batch-size",
        type=int,
        default=DEFAULT_DB_BATCH_SIZE,
        help=f"Records fetched per database batch (default: {DEFAULT_DB_BATCH_SIZE})",
    )
    parser.add_argument(
        "--inference-batch-size",
        type=int,
        default=DEFAULT_INFERENCE_BATCH_SIZE,
        help=f"Records processed per inference batch (default: {DEFAULT_INFERENCE_BATCH_SIZE})",
    )
    parser.add_argument(
        "--resume-from",
        type=int,
        default=None,
        help="Resume from primary key watermark (records with id > resume_from)",
    )
    
    args = parser.parse_args()

    # ── Validate arguments ────────────────────────────────────────────────────
    if args.tenant_id is not None and args.workspace_id is None:
        logger.error("Error: --tenant-id requires --workspace-id")
        return 1
    
    if args.db_batch_size < 1:
        logger.error("Error: --db-batch-size must be >= 1")
        return 1
    
    if args.inference_batch_size < 1:
        logger.error("Error: --inference-batch-size must be >= 1")
        return 1

    logger.info("Starting embedding backfill")
    logger.info(
        "Configuration: model=%s version=%s db_batch=%s inference_batch=%s",
        args.model_name,
        args.model_version,
        args.db_batch_size,
        args.inference_batch_size,
    )
    
    if args.resume_from is not None:
        logger.info("Resuming from primary key watermark: %s", args.resume_from)
    
    if args.workspace_id is not None:
        logger.info(
            "Workspace-scoped backfill: workspace_id=%s%s",
            args.workspace_id,
            f" tenant_id={args.tenant_id}" if args.tenant_id else "",
        )

    try:
        model = load_embedding_model()
    except Exception:
        logger.exception("Failed to load embedding model")
        return 1

    session = SessionLocal()

    try:
        # Backfill triggers (catalog - always global)
        logger.info("Backfilling triggers...")
        trigger_stats = backfill_triggers(
            session=session,
            model=model,
            force=args.force,
            model_name=args.model_name,
            model_version=args.model_version,
            db_batch_size=args.db_batch_size,
            inference_batch_size=args.inference_batch_size,
            resume_from=args.resume_from,
        )
        log_stats("Trigger", trigger_stats)

        # Backfill actions (catalog - always global)
        logger.info("Backfilling actions...")
        action_stats = backfill_actions(
            session=session,
            model=model,
            force=args.force,
            model_name=args.model_name,
            model_version=args.model_version,
            db_batch_size=args.db_batch_size,
            inference_batch_size=args.inference_batch_size,
            resume_from=args.resume_from,
        )
        log_stats("Action", action_stats)

        # Backfill business rules (workspace-scoped)
        logger.info("Backfilling business rules...")
        business_rule_stats = backfill_business_rules(
            session=session,
            model=model,
            force=args.force,
            workspace_id=args.workspace_id,
            tenant_id=args.tenant_id,
            model_name=args.model_name,
            model_version=args.model_version,
            db_batch_size=args.db_batch_size,
            inference_batch_size=args.inference_batch_size,
            resume_from=args.resume_from,
        )
        log_stats("BusinessRule", business_rule_stats)

        # ── Final summary ────────────────────────────────────────────────────
        total_updated = (
            trigger_stats.updated
            + action_stats.updated
            + business_rule_stats.updated
        )
        total_skipped = (
            trigger_stats.skipped
            + action_stats.skipped
            + business_rule_stats.skipped
        )
        total_failed = (
            trigger_stats.failed
            + action_stats.failed
            + business_rule_stats.failed
        )
        total_batches = (
            trigger_stats.processed_batches
            + action_stats.processed_batches
            + business_rule_stats.processed_batches
        )

        logger.info(
            "Backfill complete: updated=%s skipped=%s failed=%s batches_processed=%s",
            total_updated,
            total_skipped,
            total_failed,
            total_batches,
        )

        if total_failed > 0:
            logger.warning(
                "Backfill encountered %s failures. "
                "Previously committed batches remain in database. "
                "Use --resume-from to retry failed records.",
                total_failed,
            )
            # Don't fail the entire operation—previous batches succeeded
            return 0

        return 0

    except ValueError as e:
        logger.error("Validation error: %s", str(e))
        return 1

    except Exception:
        logger.exception("Backfill failed")
        return 1

    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())

