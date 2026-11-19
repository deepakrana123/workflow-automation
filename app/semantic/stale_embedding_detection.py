"""
Stale Embedding Detection Utilities (Phase 2B)

This module provides helpers to detect embeddings that are stale (generated with
an older model version) without triggering automatic regeneration. Detection is
purely query-based; regeneration is explicit and requires manual action.

Pattern matching enables users to:
1. Detect embeddings from old model versions
2. Find embeddings missing metadata (backfilled before Phase 2B)
3. Query generation timestamps for audit/compliance

All detection is done via SQL queries; no automatic regeneration occurs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, and_, or_

from app.models.action_definitions import ActionDefinition
from app.models.trigger_definitions import TriggerDefinition
from app.models.workflow_business_rule import WorkflowBusinessRule


# Phase 2B model identifiers
CURRENT_MODEL_NAME = "BAAI/bge-small-en-v1.5"
CURRENT_MODEL_VERSION = "1.5"


def find_stale_action_embeddings(
    session: Any,
    target_model_name: str = CURRENT_MODEL_NAME,
    target_model_version: str = CURRENT_MODEL_VERSION,
) -> list[ActionDefinition]:
    """
    Find ActionDefinition records with stale embeddings.
    
    Returns records where:
    - Embedding exists (not NULL)
    - Model name/version differs from target, OR
    - Model metadata is missing (backfilled pre-Phase 2B)
    
    Args:
        session: SQLAlchemy session
        target_model_name: Expected model name (default: BAAI/bge-small-en-v1.5)
        target_model_version: Expected model version (default: 1.5)
    
    Returns:
        List of ActionDefinition with stale embeddings
    """
    return session.scalars(
        select(ActionDefinition).filter(
            and_(
                ActionDefinition.embedding.isnot(None),
                or_(
                    ActionDefinition.embedding_model_name != target_model_name,
                    ActionDefinition.embedding_model_version != target_model_version,
                    ActionDefinition.embedding_model_name.is_(None),
                    ActionDefinition.embedding_model_version.is_(None),
                ),
            )
        )
    ).all()


def find_stale_trigger_embeddings(
    session: Any,
    target_model_name: str = CURRENT_MODEL_NAME,
    target_model_version: str = CURRENT_MODEL_VERSION,
) -> list[TriggerDefinition]:
    """
    Find TriggerDefinition records with stale embeddings.
    
    Returns records where:
    - Embedding exists (not NULL)
    - Model name/version differs from target, OR
    - Model metadata is missing (backfilled pre-Phase 2B)
    
    Args:
        session: SQLAlchemy session
        target_model_name: Expected model name (default: BAAI/bge-small-en-v1.5)
        target_model_version: Expected model version (default: 1.5)
    
    Returns:
        List of TriggerDefinition with stale embeddings
    """
    return session.scalars(
        select(TriggerDefinition).filter(
            and_(
                TriggerDefinition.embedding.isnot(None),
                or_(
                    TriggerDefinition.embedding_model_name != target_model_name,
                    TriggerDefinition.embedding_model_version != target_model_version,
                    TriggerDefinition.embedding_model_name.is_(None),
                    TriggerDefinition.embedding_model_version.is_(None),
                ),
            )
        )
    ).all()


def find_stale_business_rule_embeddings(
    session: Any,
    target_model_name: str = CURRENT_MODEL_NAME,
    target_model_version: str = CURRENT_MODEL_VERSION,
    workspace_id: int | None = None,
) -> list[WorkflowBusinessRule]:
    """
    Find WorkflowBusinessRule records with stale embeddings.
    
    Returns records where:
    - Embedding exists (not NULL)
    - Model name/version differs from target, OR
    - Model metadata is missing (backfilled pre-Phase 2B)
    
    Args:
        session: SQLAlchemy session
        target_model_name: Expected model name (default: BAAI/bge-small-en-v1.5)
        target_model_version: Expected model version (default: 1.5)
        workspace_id: Optional workspace_id to scope query (None = all workspaces)
    
    Returns:
        List of WorkflowBusinessRule with stale embeddings
    """
    q = select(WorkflowBusinessRule).filter(
        and_(
            WorkflowBusinessRule.embedding.isnot(None),
            or_(
                WorkflowBusinessRule.embedding_model_name != target_model_name,
                WorkflowBusinessRule.embedding_model_version != target_model_version,
                WorkflowBusinessRule.embedding_model_name.is_(None),
                WorkflowBusinessRule.embedding_model_version.is_(None),
            ),
        )
    )

    if workspace_id is not None:
        from app.models.workflow_knowledge import WorkflowKnowledge
        q = q.join(WorkflowKnowledge).filter(
            WorkflowKnowledge.workspace_id == workspace_id
        )

    return session.scalars(q).all()


def find_missing_metadata_actions(
    session: Any,
) -> list[ActionDefinition]:
    """
    Find ActionDefinition records with embeddings but missing metadata.
    
    Returns records where:
    - Embedding exists (not NULL)
    - Model name or version is NULL
    
    These are embeddings backfilled before Phase 2B metadata columns existed.
    
    Args:
        session: SQLAlchemy session
    
    Returns:
        List of ActionDefinition with missing metadata
    """
    return session.scalars(
        select(ActionDefinition).filter(
            and_(
                ActionDefinition.embedding.isnot(None),
                or_(
                    ActionDefinition.embedding_model_name.is_(None),
                    ActionDefinition.embedding_model_version.is_(None),
                ),
            )
        )
    ).all()


def find_missing_metadata_triggers(
    session: Any,
) -> list[TriggerDefinition]:
    """
    Find TriggerDefinition records with embeddings but missing metadata.
    
    Returns records where:
    - Embedding exists (not NULL)
    - Model name or version is NULL
    
    These are embeddings backfilled before Phase 2B metadata columns existed.
    
    Args:
        session: SQLAlchemy session
    
    Returns:
        List of TriggerDefinition with missing metadata
    """
    return session.scalars(
        select(TriggerDefinition).filter(
            and_(
                TriggerDefinition.embedding.isnot(None),
                or_(
                    TriggerDefinition.embedding_model_name.is_(None),
                    TriggerDefinition.embedding_model_version.is_(None),
                ),
            )
        )
    ).all()


def find_missing_metadata_business_rules(
    session: Any,
    workspace_id: int | None = None,
) -> list[WorkflowBusinessRule]:
    """
    Find WorkflowBusinessRule records with embeddings but missing metadata.
    
    Returns records where:
    - Embedding exists (not NULL)
    - Model name or version is NULL
    
    These are embeddings backfilled before Phase 2B metadata columns existed.
    
    Args:
        session: SQLAlchemy session
        workspace_id: Optional workspace_id to scope query (None = all workspaces)
    
    Returns:
        List of WorkflowBusinessRule with missing metadata
    """
    q = select(WorkflowBusinessRule).filter(
        and_(
            WorkflowBusinessRule.embedding.isnot(None),
            or_(
                WorkflowBusinessRule.embedding_model_name.is_(None),
                WorkflowBusinessRule.embedding_model_version.is_(None),
            ),
        )
    )

    if workspace_id is not None:
        from app.models.workflow_knowledge import WorkflowKnowledge
        q = q.join(WorkflowKnowledge).filter(
            WorkflowKnowledge.workspace_id == workspace_id
        )

    return session.scalars(q).all()


def count_stale_embeddings_by_model(
    session: Any,
    target_model_name: str = CURRENT_MODEL_NAME,
) -> dict[str | None, int]:
    """
    Count embeddings grouped by model_name (including NULL for missing metadata).
    
    This query enables audit reports: "How many embeddings are from old models?"
    
    Args:
        session: SQLAlchemy session
        target_model_name: Model name to exclude from count (default: current)
    
    Returns:
        Dict mapping model_name (or None) to count
    """
    from sqlalchemy import func

    # Count actions
    action_counts = {}
    action_results = session.execute(
        select(
            ActionDefinition.embedding_model_name,
            func.count(ActionDefinition.id).label("cnt"),
        ).filter(
            and_(
                ActionDefinition.embedding.isnot(None),
                ActionDefinition.embedding_model_name != target_model_name,
            )
        ).group_by(ActionDefinition.embedding_model_name)
    ).all()

    for model_name, cnt in action_results:
        action_counts[model_name] = action_counts.get(model_name, 0) + cnt

    # Count triggers
    trigger_results = session.execute(
        select(
            TriggerDefinition.embedding_model_name,
            func.count(TriggerDefinition.id).label("cnt"),
        ).filter(
            and_(
                TriggerDefinition.embedding.isnot(None),
                TriggerDefinition.embedding_model_name != target_model_name,
            )
        ).group_by(TriggerDefinition.embedding_model_name)
    ).all()

    for model_name, cnt in trigger_results:
        action_counts[model_name] = action_counts.get(model_name, 0) + cnt

    # Count business rules
    rule_results = session.execute(
        select(
            WorkflowBusinessRule.embedding_model_name,
            func.count(WorkflowBusinessRule.id).label("cnt"),
        ).filter(
            and_(
                WorkflowBusinessRule.embedding.isnot(None),
                WorkflowBusinessRule.embedding_model_name != target_model_name,
            )
        ).group_by(WorkflowBusinessRule.embedding_model_name)
    ).all()

    for model_name, cnt in rule_results:
        action_counts[model_name] = action_counts.get(model_name, 0) + cnt

    return action_counts


def get_embedding_generation_window(
    session: Any,
) -> tuple[datetime | None, datetime | None]:
    """
    Get the earliest and latest embedding generation times across all tables.
    
    Useful for audit/compliance: "When was the oldest embedding generated?"
    
    Args:
        session: SQLAlchemy session
    
    Returns:
        Tuple of (earliest_timestamp, latest_timestamp), or (None, None) if
        no embeddings with metadata exist
    """
    from sqlalchemy import func

    min_generated = session.execute(
        select(
            func.min(
                func.least(
                    func.min(ActionDefinition.embedding_generated_at),
                    func.min(TriggerDefinition.embedding_generated_at),
                    func.min(WorkflowBusinessRule.embedding_generated_at),
                )
            )
        )
    ).scalar()

    max_generated = session.execute(
        select(
            func.max(
                func.greatest(
                    func.max(ActionDefinition.embedding_generated_at),
                    func.max(TriggerDefinition.embedding_generated_at),
                    func.max(WorkflowBusinessRule.embedding_generated_at),
                )
            )
        )
    ).scalar()

    return (min_generated, max_generated)
