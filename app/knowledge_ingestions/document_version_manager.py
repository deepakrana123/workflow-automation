"""
app/knowledge_ingestions/document_version_manager.py

Document version management for Phase 6 hardening.

Responsibilities:
1. Prevent multiple WorkflowKnowledge rows per DocumentVersion (deduplication)
2. Preserve rule provenance during re-extraction (immutable source_brd_document_id)
3. Define and enforce active version semantics
4. Validate version chain integrity

Design:
- Re-extraction creates NEW WorkflowKnowledge, does NOT update old rules
- Active version = latest completed DocumentVersion (implicit)
- Immutable source_brd_document_id on WorkflowBusinessRule
- Fail loudly if provenance chain broken
"""

from app.core.logger import logger
from app.models.document_version import DocumentVersion, VersionStatus
from app.models.brd_document import BRDDocument
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workflow_business_rule import WorkflowBusinessRule
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import Session


class DocumentVersionManager:
    """Manages document versioning and active version semantics."""

    @staticmethod
    def get_active_document_version(
        db: Session,
        brd_document_id: int,
    ) -> DocumentVersion | None:
        """
        Get the active (latest completed) version of a document.

        Active version = most recent DocumentVersion with status=COMPLETED.

        Args:
            db: SQLAlchemy session
            brd_document_id: BRDDocument ID

        Returns:
            Latest completed DocumentVersion, or None if none completed.
        """
        return db.scalar(
            select(DocumentVersion)
            .filter(
                and_(
                    DocumentVersion.document_id == brd_document_id,
                    DocumentVersion.status == VersionStatus.COMPLETED.value,
                )
            )
            .order_by(desc(DocumentVersion.version_number))
            .limit(1)
        )

    @staticmethod
    def is_duplicate_knowledge(
        db: Session,
        document_version_id: int,
    ) -> bool:
        """
        Check if WorkflowKnowledge already exists for this version.

        A version should only have one WorkflowKnowledge row (1:1 relationship).
        If two attempts both complete, the second should fail with duplicate.

        Args:
            db: SQLAlchemy session
            document_version_id: DocumentVersion ID

        Returns:
            True if WorkflowKnowledge already exists for this version.
        """
        existing = db.scalar(
            select(func.count(WorkflowKnowledge.id)).filter(
                WorkflowKnowledge.document_version_id == document_version_id
            )
        )
        return existing > 0

    @staticmethod
    def validate_provenance_chain(
        db: Session,
        rule_id: int,
        expected_workspace_id: int,
        expected_tenant_id: int,
    ) -> bool:
        """
        Validate that a rule's provenance chain is intact.

        Walks: WorkflowBusinessRule → BRDDocument → Workspace → Tenant

        Args:
            db: SQLAlchemy session
            rule_id: WorkflowBusinessRule ID
            expected_workspace_id: Expected workspace for this rule
            expected_tenant_id: Expected tenant for this rule

        Returns:
            True if chain is intact, False if broken.

        Logs error if chain broken.
        """
        rule = db.scalar(
            select(WorkflowBusinessRule).filter(
                WorkflowBusinessRule.id == rule_id
            )
        )
        if rule is None:
            logger.error(
                "document_version_provenance_rule_not_found",
                extra={"extra_data": {"rule_id": rule_id}},
            )
            return False

        if rule.source_brd_document_id is None:
            logger.warning(
                "document_version_provenance_null_source",
                extra={
                    "extra_data": {
                        "rule_id": rule_id,
                        "expected_workspace_id": expected_workspace_id,
                    }
                },
            )
            return False

        brd_document = db.scalar(
            select(BRDDocument).filter(
                BRDDocument.id == rule.source_brd_document_id
            )
        )
        if brd_document is None:
            logger.error(
                "document_version_provenance_orphaned_rule",
                extra={
                    "extra_data": {
                        "rule_id": rule_id,
                        "brd_document_id": rule.source_brd_document_id,
                    }
                },
            )
            return False

        if brd_document.workspace_id != expected_workspace_id:
            logger.error(
                "document_version_provenance_workspace_mismatch",
                extra={
                    "extra_data": {
                        "rule_id": rule_id,
                        "expected_workspace_id": expected_workspace_id,
                        "actual_workspace_id": brd_document.workspace_id,
                    }
                },
            )
            return False

        if brd_document.tenant_id != expected_tenant_id:
            logger.error(
                "document_version_provenance_tenant_mismatch",
                extra={
                    "extra_data": {
                        "rule_id": rule_id,
                        "expected_tenant_id": expected_tenant_id,
                        "actual_tenant_id": brd_document.tenant_id,
                    }
                },
            )
            return False

        return True

    @staticmethod
    def count_completed_versions(
        db: Session,
        brd_document_id: int,
    ) -> int:
        """
        Count how many completed versions exist for a document.

        Used to detect if multiple versions are live and might be mixed in retrieval.

        Args:
            db: SQLAlchemy session
            brd_document_id: BRDDocument ID

        Returns:
            Count of DocumentVersion records with status=COMPLETED.
        """
        return db.scalar(
            select(func.count(DocumentVersion.id)).filter(
                and_(
                    DocumentVersion.document_id == brd_document_id,
                    DocumentVersion.status == VersionStatus.COMPLETED.value,
                )
            )
        ) or 0

    @staticmethod
    def get_rules_by_document_version(
        db: Session,
        document_version_id: int,
    ) -> list[WorkflowBusinessRule]:
        """
        Get all rules extracted from a specific document version.

        Used to audit which rules came from which version.

        Args:
            db: SQLAlchemy session
            document_version_id: DocumentVersion ID

        Returns:
            List of WorkflowBusinessRule linked to this version.
        """
        # Trace: DocumentVersion → WorkflowKnowledge → WorkflowBusinessRule
        return db.scalars(
            select(WorkflowBusinessRule)
            .join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowBusinessRule.workflow_knowledge_id,
            )
            .filter(
                WorkflowKnowledge.document_version_id == document_version_id
            )
        ).all()


class ProvenanceValidator:
    """Validates and reports on provenance chain integrity."""

    @staticmethod
    def validate_workspace_wide(
        db: Session,
        workspace_id: int,
    ) -> dict[str, int]:
        """
        Validate all rules in a workspace have valid provenance.

        Returns dict with:
            - total_rules: count of all WorkflowBusinessRule
            - rules_with_provenance: rules with valid source_brd_document_id
            - rules_missing_provenance: rules with NULL source_brd_document_id
            - rules_orphaned: rules pointing to deleted BRDDocument

        Args:
            db: SQLAlchemy session
            workspace_id: Workspace ID

        Returns:
            Dictionary with validation results.
        """
        stats = {
            "total_rules": 0,
            "rules_with_provenance": 0,
            "rules_missing_provenance": 0,
            "rules_orphaned": 0,
        }

        # Count total rules in workspace
        stats["total_rules"] = db.scalar(
            select(func.count(WorkflowBusinessRule.id))
            .join(WorkflowKnowledge)
            .filter(WorkflowKnowledge.workspace_id == workspace_id)
        ) or 0

        # Count with valid provenance
        stats["rules_with_provenance"] = db.scalar(
            select(func.count(WorkflowBusinessRule.id))
            .join(WorkflowKnowledge)
            .filter(
                and_(
                    WorkflowKnowledge.workspace_id == workspace_id,
                    WorkflowBusinessRule.source_brd_document_id.isnot(None),
                )
            )
        ) or 0

        # Count missing provenance (NULL source_brd_document_id)
        stats["rules_missing_provenance"] = db.scalar(
            select(func.count(WorkflowBusinessRule.id))
            .join(WorkflowKnowledge)
            .filter(
                and_(
                    WorkflowKnowledge.workspace_id == workspace_id,
                    WorkflowBusinessRule.source_brd_document_id.is_(None),
                )
            )
        ) or 0

        # Count orphaned provenance (source_brd_document_id pointing to nonexistent row)
        # This is a left join that finds rules where source_brd_document_id is not NULL
        # but BRDDocument.id is NULL (indicating the document was deleted)
        orphaned_count = db.scalar(
            select(func.count(WorkflowBusinessRule.id))
            .join(WorkflowKnowledge)
            .join(
                BRDDocument,
                BRDDocument.id == WorkflowBusinessRule.source_brd_document_id,
                isouter=True,
            )
            .filter(
                and_(
                    WorkflowKnowledge.workspace_id == workspace_id,
                    WorkflowBusinessRule.source_brd_document_id.isnot(None),
                    BRDDocument.id.is_(None),
                )
            )
        ) or 0
        stats["rules_orphaned"] = orphaned_count

        # Log if any issues found
        if stats["rules_missing_provenance"] > 0:
            logger.warning(
                "document_version_validation_missing_provenance",
                extra={
                    "extra_data": {
                        "workspace_id": workspace_id,
                        "count": stats["rules_missing_provenance"],
                    }
                },
            )

        if stats["rules_orphaned"] > 0:
            logger.error(
                "document_version_validation_orphaned_rules",
                extra={
                    "extra_data": {
                        "workspace_id": workspace_id,
                        "count": stats["rules_orphaned"],
                    }
                },
            )

        return stats
