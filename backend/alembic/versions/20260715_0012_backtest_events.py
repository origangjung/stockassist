"""Store event-driven backtest audit events."""

from alembic import op
import sqlalchemy as sa

revision = "20260715_0012"
down_revision = "20260714_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "backtest_results",
        sa.Column(
            "events",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )
    with op.batch_alter_table("backtest_results") as batch_op:
        batch_op.alter_column(
            "events",
            existing_type=sa.JSON(),
            existing_nullable=False,
            server_default=None,
        )


def downgrade() -> None:
    with op.batch_alter_table("backtest_results") as batch_op:
        batch_op.drop_column("events")
