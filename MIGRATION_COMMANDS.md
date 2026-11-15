# Migration: Add evaluation_status to BusinessRuleDefinition

## Overview
This migration adds a nullable `evaluation_status` column to the `business_rule_definitions` table to classify rule evaluability and runtime behavior.

---

## Step 1: Create Alembic Migration File

Run this command to auto-generate a migration:

```bash
cd C:\Users\Devendra\projects\mflows
.venv312\Scripts\alembic.exe revision --autogenerate -m "add_evaluation_status_to_business_rule_definition"
```

This will create a file like `alembic/versions/XXXXX_add_evaluation_status_to_business_rule_definition.py`

---

## Step 2: Review and Edit the Migration File

The auto-generated migration should contain something like:

```python
def upgrade():
    op.add_column('business_rule_definitions', 
        sa.Column('evaluation_status', sa.String(length=32), nullable=True)
    )
    op.create_index('ix_business_rule_definitions_evaluation_status', 
        'business_rule_definitions', ['evaluation_status'], unique=False)
    op.create_check_constraint(
        'ck_business_rule_evaluation_status',
        'business_rule_definitions',
        "evaluation_status IS NULL OR evaluation_status IN ('EVALUABLE','INFORMATIONAL','PARTIAL','UNSUPPORTED','INVALID')"
    )

def downgrade():
    op.drop_constraint('ck_business_rule_evaluation_status', 'business_rule_definitions')
    op.drop_index('ix_business_rule_definitions_evaluation_status', 'business_rule_definitions')
    op.drop_column('business_rule_definitions', 'evaluation_status')
```

**If the constraint is not auto-generated**, add it manually to the upgrade() function above as shown.

---

## Step 3: Run the Migration

Execute the migration to apply it to your database:

```bash
cd C:\Users\Devendra\projects\mflows
.venv312\Scripts\alembic.exe upgrade head
```

---

## Step 4: Verify the Migration

Verify the column was added correctly:

```bash
.venv312\Scripts\python.exe -c "from app.models.business_rule_definition import BusinessRuleDefinition; from sqlalchemy.inspection import inspect; m = inspect(BusinessRuleDefinition); cols = [c.name for c in m.columns]; print('✓ evaluation_status exists' if 'evaluation_status' in cols else '✗ evaluation_status missing'); print('Columns:', cols)"
```

---

## Step 5: Verify Data Integrity

Check that existing rules were not affected:

```bash
.venv312\Scripts\python.exe << 'PYTHON'
from app.db.session import get_db
from app.models.business_rule_definition import BusinessRuleDefinition

db = next(get_db())
total = db.query(BusinessRuleDefinition).count()
with_status = db.query(BusinessRuleDefinition).filter(BusinessRuleDefinition.evaluation_status.isnot(None)).count()
print(f"Total rules: {total}")
print(f"Rules with status: {with_status}")
print(f"Rules with NULL status (legacy): {total - with_status}")
print("✓ Backward compatibility preserved: existing rules have NULL evaluation_status")
PYTHON
```

---

## Rollback (If Needed)

If you need to rollback the migration:

```bash
cd C:\Users\Devendra\projects\mflows
.venv312\Scripts\alembic.exe downgrade -1
```

---

## Notes

- The `evaluation_status` column is **nullable** for backward compatibility
- All **existing records** will have `NULL` values
- The **CHECK constraint** ensures only valid values can be inserted going forward
- An **index** is created for query performance when filtering by status
- No data loss occurs — this is a purely additive change

---

## Migration File Location

After running `alembic revision --autogenerate`, the migration will be created at:

```
alembic/versions/<timestamp>_add_evaluation_status_to_business_rule_definition.py
```

Check this file and commit it to version control.
