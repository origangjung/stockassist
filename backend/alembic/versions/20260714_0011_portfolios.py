"""Create broker account links and latest holding snapshots."""

from alembic import op
import sqlalchemy as sa

revision = "20260714_0011"
down_revision = "20260714_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "broker_accounts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("provider", sa.String(24), nullable=False),
        sa.Column("account_seq", sa.Integer(), nullable=False),
        sa.Column("account_no_masked", sa.String(24), nullable=False),
        sa.Column("account_type", sa.String(48), nullable=False),
        sa.Column("sync_status", sa.String(24), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("provider", "account_seq", name="uq_broker_provider_account_seq"),
    )
    op.create_table(
        "holdings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("provider", sa.String(24), nullable=False),
        sa.Column("account_seq", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("market_country", sa.String(8), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("quantity", sa.Numeric(24, 6), nullable=False),
        sa.Column("last_price", sa.Numeric(24, 6), nullable=False),
        sa.Column("average_purchase_price", sa.Numeric(24, 6), nullable=False),
        sa.Column("purchase_amount", sa.Numeric(24, 6), nullable=False),
        sa.Column("market_value", sa.Numeric(24, 6), nullable=False),
        sa.Column("market_value_after_cost", sa.Numeric(24, 6), nullable=False),
        sa.Column("profit_loss", sa.Numeric(24, 6), nullable=False),
        sa.Column("profit_loss_after_cost", sa.Numeric(24, 6), nullable=False),
        sa.Column("profit_rate", sa.Numeric(12, 8), nullable=False),
        sa.Column("profit_rate_after_cost", sa.Numeric(12, 8), nullable=False),
        sa.Column("daily_profit_loss", sa.Numeric(24, 6), nullable=False),
        sa.Column("daily_profit_rate", sa.Numeric(12, 8), nullable=False),
        sa.Column("commission", sa.Numeric(24, 6), nullable=True),
        sa.Column("tax", sa.Numeric(24, 6), nullable=True),
        sa.Column("data_as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "provider", "account_seq", "symbol", name="uq_holding_provider_account_symbol"
        ),
    )


def downgrade() -> None:
    op.drop_table("holdings")
    op.drop_table("broker_accounts")
