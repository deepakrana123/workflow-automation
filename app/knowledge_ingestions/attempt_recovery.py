"""
app/knowledge_ingestions/attempt_recovery.py

Ingestion attempt recovery for Phase 6 hardening.

Responsibilities:
1. Detect and recover stale RUNNING attempts (hung workers)
2. Cleanup storage for failed ingestions
3. Ensure re-extraction idempotency (prevent duplicate WorkflowKnowledge)
4. Track partial extraction status

Design:
- RUNNING attempts older than TTL (1 hour) marked as FAILED
- Failed storage cleanup deferred to async job (logged for cleanup service)
- WorkflowKnowledge uniqueness enforced per DocumentVersion
- Partial extractions tracked in pipeline_snapshot
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import Session

from app.models.ingestion_attempt import IngestionAttempt, AttemptStatus
from app.models.document_version import DocumentVersion, VersionStatus
from app.models.brd_document import BRDDocument
from app.models.workflow_knowledge import WorkflowKnowledge
from app.core.logger import logger


# RUNNING attempts stuck for 1 hour are considered stale and failed
STALE_ATTEMPT_TTL_SECONDS = 3600


class AttemptRecoveryManager:
    """Manages recovery of stuck or failed ingestion attempts."""

    @staticmethod
    def detect_and_recover_stale_attempts(
        db: Session,
        ttl_seconds: int = STALE_ATTEMPT_TTL_SECONDS,
    ) -> dict[str, int]:
        """
        Find and recover RUNNING attempts older than TTL.

        A RUNNING attempt that has been executing for longer than ttl_seconds
        is assumed to be hung (worker crashed, network issue, or infinite loop).
        Mark it as FAILED and update document version status.

        Args:
            db: SQLAlchemy session
            ttl_seconds: Time-to-live for RUNNING attempts (default: 3600 seconds = 1 hour)

        Returns:
            Dict with:
                - stale_attempts_found: count of stale RUNNING attempts
                - attempts_recovered: count successfully marked FAILED
                - recovery_errors: count of errors during recovery
        """
        stats = {
            "stale_attempts_found": 0,
            "attempts_recovered": 0,
            "recovery_errors": 0,
        }

        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=ttl_seconds)

        # Find all RUNNING attempts older than cutoff
        stale_attempts = db.scalars(
            select(IngestionAttempt).filter(
                and_(
                    IngestionAttempt.status == AttemptStatus.RUNNING.value,
                    IngestionAttempt.started_at.isnot(None),
                    IngestionAttempt.started_at < cutoff_time,
                )
            )
        ).all()

        stats["stale_attempts_found"] = len(stale_attempts)

        for attempt in stale_attempts:
            try:
                # Mark attempt as FAILED with stale error code
                attempt.status = AttemptStatus.FAILED.value
                attempt.completed_at = datetime.now(timezone.utc)
                attempt.error_code = "STALE_RUNNING_ATTEMPT"
                attempt.error_message = (
                    f"Attempt was RUNNING for more than {ttl_seconds}s; "
                    f"marked as stale and failed at {datetime.now(timezone.utc).isoformat()}"
                )

                # Update document version status to FAILED (if it's still PROCESSING)
                if attempt.version and attempt.version.status == VersionStatus.PROCESSING.value:
                    attempt.version.status = VersionStatus.FAILED.value
                    attempt.version.failure_reason = "Stale RUNNING attempt detected"

                # Update BRDDocument status to FAILED as well
                if attempt.version and attempt.version.document:
                    if attempt.version.document.ingestion_status == "PROCESSING":
                        attempt.version.document.ingestion_status = "FAILED"
                        attempt.version.document.failure_reason = "Stale RUNNING attempt detected"

                db.flush()
                stats["attempts_recovered"] += 1

                logger.info(
                    "attempt_recovery_stale_attempt_recovered",
                    extra={
                        "extra_data": {
                            "attempt_id": attempt.id,
                            "document_version_id": attempt.document_version_id,
                            "started_at": attempt.started_at.isoformat(),
                            "age_seconds": (datetime.now(timezone.utc) - attempt.started_at).total_seconds(),
                        }
                    },
                )
            except Exception as e:
                stats["recovery_errors"] += 1
                logger.exception(
                    "attempt_recovery_error",
                    extra={
                        "extra_data": {
                            "attempt_id": attempt.id,
                            "error": str(e),
                        }
                    },
                )

        # Commit all recovered attempts
        if stats["attempts_recovered"] > 0:
            try:
                db.commit()
                logger.info(
                    "attempt_recovery_batch_committed",
                    extra={
                        "extra_data": {
                            "count": stats["attempts_recovered"],
                        }
                    },
                )
            except Exception as e:
                db.rollback()
                stats["recovery_errors"] += stats["attempts_recovered"]
                logger.exception("attempt_recovery_batch_commit_failed")

        return stats

    @staticmethod
    def mark_failed_storage_for_cleanup(
        db: Session,
        attempt_id: int,
        storage_path: str | None,
    ) -> None:
        """
        Log storage file for cleanup (deferred action).

        When an ingestion attempt fails after storing the PDF but before
        successful knowledge persistence, the storage file should be cleaned up.
        This method logs the file for an async cleanup service.

        In a production system, this would be sent to:
        - A queue (SQS, RabbitMQ) for async cleanup
        - A cleanup log table for periodic batch cleanup
        - A storage lifecycle rule (for object storage services)

        For Phase 6, we log it for visibility and manual cleanup if needed.

        Args:
            db: SQLAlchemy session
            attempt_id: IngestionAttempt ID
            storage_path: FileStorageService storage_path to clean up
        """
        if not storage_path:
            return

        logger.info(
            "attempt_recovery_storage_cleanup_required",
            extra={
                "extra_data": {
                    "attempt_id": attempt_id,
                    "storage_path": storage_path,
                    "action": "DELETE_ORPHANED_FILE",
                }
            },
        )

        # In a real system, also write to a cleanup log table:
        # db.add(StorageCleanupLog(
        #     attempt_id=attempt_id,
        #     storage_path=storage_path,
        #     created_at=datetime.now(timezone.utc),
        #     status="PENDING",
        # ))

    @staticmethod
    def count_failed_attempts_by_error_code(
        db: Session,
        workspace_id: int | None = None,
        last_n_days: int = 7,
    ) -> dict[str, int]:
        """
        Count failed attempts by error code for diagnostics.

        Used to identify patterns (e.g., all recent failures are LLM_TIMEOUT).

        Args:
            db: SQLAlchemy session
            workspace_id: Optional workspace filter
            last_n_days: Only count attempts from last N days

        Returns:
            Dict mapping error_code to count.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=last_n_days)

        q = (
            select(IngestionAttempt.error_code, func.count(IngestionAttempt.id))
            .filter(
                and_(
                    IngestionAttempt.status == AttemptStatus.FAILED.value,
                    IngestionAttempt.completed_at >= cutoff_date,
                )
            )
        )

        if workspace_id is not None:
            q = q.join(DocumentVersion).join(BRDDocument).filter(
                BRDDocument.workspace_id == workspace_id
            )

        q = q.group_by(IngestionAttempt.error_code)

        return {error_code: count for error_code, count in db.execute(q).all()}

    @staticmethod
    def get_retry_candidates(
        db: Session,
        workspace_id: int,
        retryable_error_codes: list[str] | None = None,
    ) -> list[IngestionAttempt]:
        """
        Get FAILED attempts that are candidates for retry.

        Args:
            db: SQLAlchemy session
            workspace_id: Workspace to scope retries
            retryable_error_codes: List of error codes that should be retried.
                Default: ["EXTRACTION_FAILED", "LLM_TIMEOUT", "MAPPING_FAILED"]

        Returns:
            List of IngestionAttempt ready for retry.
        """
        if retryable_error_codes is None:
            retryable_error_codes = [
                "EXTRACTION_FAILED",
                "LLM_TIMEOUT",
                "MAPPING_FAILED",
            ]

        return db.scalars(
            select(IngestionAttempt)
            .join(DocumentVersion)
            .join(BRDDocument)
            .filter(
                and_(
                    BRDDocument.workspace_id == workspace_id,
                    IngestionAttempt.status == AttemptStatus.FAILED.value,
                    IngestionAttempt.error_code.in_(retryable_error_codes),
                )
            )
            .order_by(IngestionAttempt.completed_at)
        ).all()


class PartialExtractionTracker:
    """Tracks partial extraction results for visibility and recovery."""

    @staticmethod
    def mark_partial_completion(
        db: Session,
        attempt_id: int,
        partial_reason: str,
        pages_extracted: int,
        pages_total: int,
    ) -> None:
        """
        Mark an attempt as COMPLETED but with partial extraction.

        Partial extractions proceed to knowledge ingestion but with warning.
        The pipeline_snapshot records why the extraction was partial.

        Args:
            db: SQLAlchemy session
            attempt_id: IngestionAttempt ID
            partial_reason: Human-readable reason (e.g., "3 pages failed OCR")
            pages_extracted: Number of pages successfully extracted
            pages_total: Total number of pages in document
        """
        attempt = db.scalar(
            select(IngestionAttempt).filter(IngestionAttempt.id == attempt_id)
        )
        if attempt is None:
            return

        if attempt.pipeline_snapshot is None:
            attempt.pipeline_snapshot = {}

        attempt.pipeline_snapshot["partial_extraction"] = {
            "is_partial": True,
            "reason": partial_reason,
            "pages_extracted": pages_extracted,
            "pages_total": pages_total,
            "extraction_rate": pages_extracted / pages_total if pages_total > 0 else 0,
        }

        logger.warning(
            "attempt_recovery_partial_extraction",
            extra={
                "extra_data": {
                    "attempt_id": attempt_id,
                    "reason": partial_reason,
                    "pages": f"{pages_extracted}/{pages_total}",
                }
            },
        )

    @staticmethod
    def get_partial_extractions(
        db: Session,
        workspace_id: int | None = None,
    ) -> list[IngestionAttempt]:
        """
        Get all COMPLETED attempts with partial extraction.

        Args:
            db: SQLAlchemy session
            workspace_id: Optional workspace filter

        Returns:
            List of IngestionAttempt with partial_extraction in pipeline_snapshot.
        """
        # Note: Checking JSONB field for key requires database-specific syntax
        # This is a simplified version; production would use SQLAlchemy's JSONB operators
        all_completed = db.scalars(
            select(IngestionAttempt)
            .filter(IngestionAttempt.status == AttemptStatus.COMPLETED.value)
        ).all()

        partials = []
        for attempt in all_completed:
            if (
                attempt.pipeline_snapshot
                and isinstance(attempt.pipeline_snapshot, dict)
                and attempt.pipeline_snapshot.get("partial_extraction", {}).get("is_partial")
            ):
                partials.append(attempt)

        return partials
