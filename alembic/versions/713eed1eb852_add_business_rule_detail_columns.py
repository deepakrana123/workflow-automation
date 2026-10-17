from alembic import op
import sqlalchemy as sa

revision = "713eed1eb852"
down_revision = "22694bd068a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workflow_business_rule",
        sa.Column("condition", sa.Text(), nullable=True),
    )
    op.add_column(
        "workflow_business_rule",
        sa.Column("outcome", sa.Text(), nullable=True),
    )
    op.add_column(
        "workflow_business_rule",
        sa.Column("responsible_role", sa.Text(), nullable=True),
    )
    op.add_column(
        "workflow_business_rule",
        sa.Column("threshold", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workflow_business_rule", "threshold")
    op.drop_column("workflow_business_rule", "responsible_role")
    op.drop_column("workflow_business_rule", "outcome")
    op.drop_column("workflow_business_rule", "condition")