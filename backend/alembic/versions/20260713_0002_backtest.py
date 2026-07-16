"""Create backtest run and result tables."""

from alembic import op
import sqlalchemy as sa

revision = "20260713_0002"
down_revision = "20260713_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "backtest_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("symbol", sa.String(16), nullable=False),
        sa.Column("strategy", sa.String(80), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_backtest_runs_symbol_started", "backtest_runs", ["symbol", "started_at"])
    op.create_table(
        "backtest_results",
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("backtest_runs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("equity_curve", sa.JSON(), nullable=False),
        sa.Column("trades", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    op.drop_table("backtest_results")
    op.drop_index("ix_backtest_runs_symbol_started", table_name="backtest_runs")
    op.drop_table("backtest_runs")
