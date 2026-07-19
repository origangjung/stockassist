"""Add point-in-time corporate action revision history."""

from alembic import op
import sqlalchemy as sa

revision = "20260719_0018"
down_revision = "20260719_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "stock_candles",
        sa.Column(
            "price_basis",
            sa.String(32),
            nullable=False,
            server_default="unknown",
        ),
    )
    op.create_table(
        "corporate_actions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(16), nullable=False),
        sa.Column("action_type", sa.String(24), nullable=False),
        sa.Column("event_id", sa.String(128), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("announced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("known_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price_factor", sa.Numeric(24, 12), nullable=False),
        sa.Column("volume_factor", sa.Numeric(24, 12), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("rule_version", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "action_type IN ('split', 'reverse_split', 'cash_dividend', "
            "'stock_dividend', 'rights_issue')",
            name="ck_corporate_action_type",
        ),
        sa.CheckConstraint(
            "status IN ('announced', 'confirmed', 'cancelled')",
            name="ck_corporate_action_status",
        ),
        sa.CheckConstraint("revision > 0", name="ck_corporate_action_revision"),
        sa.CheckConstraint("price_factor > 0", name="ck_corporate_action_price_factor"),
        sa.CheckConstraint("volume_factor > 0", name="ck_corporate_action_volume_factor"),
        sa.ForeignKeyConstraint(["symbol"], ["stocks.symbol"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source", "symbol", "event_id", "revision", name="uq_corporate_action_revision"
        ),
    )
    op.create_index(
        "ix_corporate_actions_symbol_effective",
        "corporate_actions",
        ["symbol", "effective_at"],
    )
    op.create_index(
        "ix_corporate_actions_symbol_known",
        "corporate_actions",
        ["symbol", "known_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_corporate_actions_symbol_known", table_name="corporate_actions")
    op.drop_index("ix_corporate_actions_symbol_effective", table_name="corporate_actions")
    op.drop_table("corporate_actions")
    op.drop_column("stock_candles", "price_basis")
