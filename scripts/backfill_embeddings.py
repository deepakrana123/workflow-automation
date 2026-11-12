
from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from typing import Any

from sentence_transformers import SentenceTransformer
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.action_definitions import ActionDefinition
from app.models.trigger_definitions import TriggerDefinition
from app.models.workflow_business_rule import WorkflowBusinessRule


MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSION = 384
BATCH_SIZE = 32

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


def load_embedding_model() -> SentenceTransformer:
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
) -> BackfillStats:
    stats = BackfillStats()

    rules = session.scalars(
        select(WorkflowBusinessRule)
    ).all()

    stats.total = len(rules)

    pending_records = []
    pending_texts = []

    for rule in rules:
        if not force and getattr(rule, "embedding", None) is not None:
            stats.skipped += 1
            continue

        try:
            text = build_business_rule_text(rule).strip()
        except Exception:
            stats.failed += 1

            logger.exception(
                "Failed to build embedding text for business rule: id=%s",
                getattr(rule, "id", None),
            )

            continue

        if not text:
            logger.warning(
                "Skipping business rule with empty text: id=%s",
                getattr(rule, "id", None),
            )

            stats.skipped += 1
            continue

        pending_records.append(rule)
        pending_texts.append(text)

    if not pending_texts:
        logger.info("No business rule embeddings to generate.")
        return stats

    logger.info(
        "Generating embeddings for %s business rules",
        len(pending_texts),
    )

    embeddings = model.encode(
        pending_texts,
        batch_size=BATCH_SIZE,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    for rule, embedding in zip(pending_records, embeddings):
        try:
            vector = embedding.tolist()

            validate_embedding(vector)

            rule.embedding = vector
            stats.updated += 1

        except Exception:
            stats.failed += 1

            logger.exception(
                "Failed to update business rule embedding: id=%s",
                getattr(rule, "id", None),
            )

    return stats


def backfill_triggers(
    session: Any,
    model: SentenceTransformer,
    force: bool = False,
) -> BackfillStats:
    stats = BackfillStats()

    triggers = session.scalars(
        select(TriggerDefinition)
    ).all()

    stats.total = len(triggers)

    pending_records = []
    pending_texts = []

    for trigger in triggers:
        if not force and getattr(trigger, "embedding", None) is not None:
            stats.skipped += 1
            continue

        try:
            text = build_trigger_text(trigger).strip()
        except Exception:
            stats.failed += 1

            logger.exception(
                "Failed to build embedding text for trigger: id=%s",
                getattr(trigger, "id", None),
            )

            continue

        if not text:
            logger.warning(
                "Skipping trigger with empty text: id=%s",
                getattr(trigger, "id", None),
            )

            stats.skipped += 1
            continue

        pending_records.append(trigger)
        pending_texts.append(text)

    if not pending_texts:
        logger.info("No trigger embeddings to generate.")
        return stats

    logger.info(
        "Generating embeddings for %s triggers",
        len(pending_texts),
    )

    embeddings = model.encode(
        pending_texts,
        batch_size=BATCH_SIZE,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    for trigger, embedding in zip(
        pending_records,
        embeddings,
    ):
        try:
            vector = embedding.tolist()

            validate_embedding(vector)

            trigger.embedding = vector
            stats.updated += 1

        except Exception:
            stats.failed += 1

            logger.exception(
                "Failed to update trigger embedding: id=%s",
                getattr(trigger, "id", None),
            )

    return stats


def backfill_actions(
    session: Any,
    model: SentenceTransformer,
    force: bool = False,
) -> BackfillStats:
    stats = BackfillStats()

    actions = session.scalars(
        select(ActionDefinition)
    ).all()

    stats.total = len(actions)

    pending_records = []
    pending_texts = []

    for action in actions:
        if not force and getattr(action, "embedding", None) is not None:
            stats.skipped += 1
            continue

        try:
            text = build_action_text(action).strip()
        except Exception:
            stats.failed += 1

            logger.exception(
                "Failed to build embedding text for action: id=%s",
                getattr(action, "id", None),
            )

            continue

        if not text:
            logger.warning(
                "Skipping action with empty text: id=%s",
                getattr(action, "id", None),
            )

            stats.skipped += 1
            continue

        pending_records.append(action)
        pending_texts.append(text)

    if not pending_texts:
        logger.info("No action embeddings to generate.")
        return stats

    logger.info(
        "Generating embeddings for %s actions",
        len(pending_texts),
    )

    embeddings = model.encode(
        pending_texts,
        batch_size=BATCH_SIZE,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    for action, embedding in zip(
        pending_records,
        embeddings,
    ):
        try:
            vector = embedding.tolist()

            validate_embedding(vector)

            action.embedding = vector
            stats.updated += 1

        except Exception:
            stats.failed += 1

            logger.exception(
                "Failed to update action embedding: id=%s",
                getattr(action, "id", None),
            )

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
    parser = argparse.ArgumentParser(description="Backfill catalog embeddings")
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help=(
            "Re-generate embeddings for ALL rows, including those that already "
            "have embeddings. Use this after changing the text format to ensure "
            "catalog and query embeddings are in the same distribution."
        ),
    )
    args = parser.parse_args()

    if args.force:
        logger.info(
            "FORCE mode: will regenerate embeddings for all rows, "
            "overwriting any existing vectors."
        )

    logger.info("Starting embedding backfill")

    logger.info(
        "Model: %s | Dimension: %s | Batch size: %s",
        MODEL_NAME,
        EMBEDDING_DIMENSION,
        BATCH_SIZE,
    )

    try:
        model = load_embedding_model()
    except Exception:
        logger.exception(
            "Failed to load or validate embedding model."
        )
        return 1

    session = SessionLocal()

    try:
        trigger_stats = backfill_triggers(
            session=session,
            model=model,
            force=args.force,
        )

        log_stats(
            "Trigger",
            trigger_stats,
        )

        action_stats = backfill_actions(
            session=session,
            model=model,
            force=args.force,
        )

        log_stats(
            "Action",
            action_stats,
        )

        business_rule_stats = backfill_business_rules(
            session=session,
            model=model,
            force=args.force,
        )

        log_stats(
            "BusinessRule",
            business_rule_stats,
        )

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

        logger.info(
            "Backfill summary: updated=%s skipped=%s failed=%s",
            total_updated,
            total_skipped,
            total_failed,
        )

        if total_failed > 0:
            logger.error(
                "Backfill encountered %s failures. Rolling back transaction.",
                total_failed,
            )

            session.rollback()
            return 1

        session.commit()

        logger.info(
            "Embedding backfill completed successfully."
        )

        return 0

    except Exception:
        session.rollback()

        logger.exception(
            "Embedding backfill failed. Transaction rolled back."
        )

        return 1

    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())

