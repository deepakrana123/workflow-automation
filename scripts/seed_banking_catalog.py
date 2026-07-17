"""
scripts/seed_banking_catalog.py

Seeds the action_definitions and trigger_definitions tables
with the comprehensive banking catalog.

Usage:
    python scripts/seed_banking_catalog.py          # Insert into DB
    python scripts/seed_banking_catalog.py --sql    # Print SQL only
    python scripts/seed_banking_catalog.py --clean  # Delete non-banking + insert

Requirements:
    - DB must be running
    - Tables action_definitions, trigger_definitions must exist
"""

import sys
import json
import argparse
from datetime import datetime, timezone

sys.path.insert(0, ".")

from scripts.banking_catalog_data import BANKING_ACTIONS, BANKING_TRIGGERS


def generate_sql() -> str:
    """Generate full SQL script for inserting the banking catalog."""
    lines = []
    now = datetime.now(timezone.utc).isoformat()

    lines.append("-- ═══════════════════════════════════════════════════")
    lines.append("-- MFlows Banking Catalog Seed Script")
    lines.append(f"-- Generated: {now}")
    lines.append(f"-- Actions: {len(BANKING_ACTIONS)}")
    lines.append(f"-- Triggers: {len(BANKING_TRIGGERS)}")
    lines.append("-- ═══════════════════════════════════════════════════")
    lines.append("")
    # Remove non-banking data (health, support, hr, medical)
    lines.append("-- Step 1: Remove non-banking triggers and actions")
    lines.append("DELETE FROM trigger_definitions WHERE workflow_type NOT IN ('finance');")
    lines.append("DELETE FROM action_definitions WHERE workflow_type NOT IN ('finance');")
    lines.append("")

    # Insert triggers
    lines.append("-- Step 2: Insert banking triggers")
    for t in BANKING_TRIGGERS:
        name = t["name"].replace("'", "''")
        display = t["display_name"].replace("'", "''")
        desc = t["description"].replace("'", "''")
        wtype = t["workflow_type"]
        aliases = json.dumps(t["aliases"]).replace("'", "''")
        lines.append(
            f"INSERT INTO trigger_definitions "
            f"(name, display_name, description, workflow_type, aliases, active, created_at, updated_at) "
            f"VALUES ('{name}', '{display}', '{desc}', '{wtype}', '{aliases}', true, NOW(), NOW()) "
            f"ON CONFLICT (name) DO UPDATE SET "
            f"display_name = EXCLUDED.display_name, "
            f"description = EXCLUDED.description, "
            f"aliases = EXCLUDED.aliases, "
            f"updated_at = NOW();"
        )
    lines.append("")

    # Insert actions
    lines.append("-- Step 3: Insert banking actions")
    for a in BANKING_ACTIONS:
        name = a["name"].replace("'", "''")
        display = a["display_name"].replace("'", "''")
        desc = a["description"].replace("'", "''")
        wtype = a["workflow_type"]
        aliases = json.dumps(a["aliases"]).replace("'", "''")
        handler = a.get("handler_name")
        handler_sql = f"'{handler}'" if handler else "NULL"
        lines.append(
            f"INSERT INTO action_definitions "
            f"(name, display_name, description, workflow_type, aliases, handler_name, active, created_at, updated_at) "
            f"VALUES ('{name}', '{display}', '{desc}', '{wtype}', '{aliases}', {handler_sql}, true, NOW(), NOW()) "
            f"ON CONFLICT (name) DO UPDATE SET "
            f"display_name = EXCLUDED.display_name, "
            f"description = EXCLUDED.description, "
            f"aliases = EXCLUDED.aliases, "
            f"handler_name = EXCLUDED.handler_name, "
            f"updated_at = NOW();"
        )
    lines.append("")
    lines.append(f"-- Done. Inserted {len(BANKING_TRIGGERS)} triggers and {len(BANKING_ACTIONS)} actions.")
    return "\n".join(lines)


def seed_via_orm():
    """Insert catalog directly using SQLAlchemy ORM."""
    from app.db.session import SessionLocal
    from app.models.action_definitions import ActionDefinition
    from app.models.trigger_definitions import TriggerDefinition

    db = SessionLocal()
    try:
        # Remove non-banking data
        deleted_t = db.query(TriggerDefinition).filter(
            TriggerDefinition.workflow_type.notin_(["finance"])
        ).delete(synchronize_session=False)
        deleted_a = db.query(ActionDefinition).filter(
            ActionDefinition.workflow_type.notin_(["finance"])
        ).delete(synchronize_session=False)
        print(f"Removed {deleted_t} non-banking triggers, {deleted_a} non-banking actions")

        # Upsert triggers
        for t in BANKING_TRIGGERS:
            existing = db.query(TriggerDefinition).filter(
                TriggerDefinition.name == t["name"]
            ).first()
            if existing:
                existing.display_name = t["display_name"]
                existing.description = t["description"]
                existing.aliases = t["aliases"]
                existing.updated_at = datetime.now(timezone.utc)
            else:
                db.add(TriggerDefinition(
                    name=t["name"],
                    display_name=t["display_name"],
                    description=t["description"],
                    workflow_type=t["workflow_type"],
                    aliases=t["aliases"],
                    active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                ))

        # Upsert actions
        for a in BANKING_ACTIONS:
            existing = db.query(ActionDefinition).filter(
                ActionDefinition.name == a["name"]
            ).first()
            if existing:
                existing.display_name = a["display_name"]
                existing.description = a["description"]
                existing.aliases = a["aliases"]
                existing.handler_name = a.get("handler_name")
                existing.updated_at = datetime.now(timezone.utc)
            else:
                db.add(ActionDefinition(
                    name=a["name"],
                    display_name=a["display_name"],
                    description=a["description"],
                    workflow_type=a["workflow_type"],
                    aliases=a["aliases"],
                    handler_name=a.get("handler_name"),
                    active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                ))

        db.commit()
        final_t = db.query(TriggerDefinition).count()
        final_a = db.query(ActionDefinition).count()
        print(f"Seed complete: {final_t} triggers, {final_a} actions in database")
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Seed banking catalog")
    parser.add_argument("--sql", action="store_true", help="Print SQL only, don't execute")
    parser.add_argument("--sql-file", type=str, help="Write SQL to file")
    args = parser.parse_args()

    print(f"Banking Catalog: {len(BANKING_ACTIONS)} actions, {len(BANKING_TRIGGERS)} triggers")

    if args.sql or args.sql_file:
        sql = generate_sql()
        if args.sql_file:
            with open(args.sql_file, "w", encoding="utf-8") as f:
                f.write(sql)
            print(f"SQL written to {args.sql_file}")
        else:
            print(sql)
    else:
        seed_via_orm()


if __name__ == "__main__":
    main()
