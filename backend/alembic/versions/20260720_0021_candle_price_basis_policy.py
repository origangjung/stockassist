"""Persist the rule version used to classify each candle price basis."""

from alembic import op
import sqlalchemy as sa

revision = "20260720_0021"
down_revision = "20260720_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "stock_candles",
        sa.Column(
            "price_basis_rule_version",
            sa.String(32),
            nullable=False,
            server_default="legacy_unknown",
        ),
    )
    op.drop_index("ix_stock_candles_price_basis_inventory", table_name="stock_candles")
    op.create_index(
        "ix_stock_candles_price_basis_inventory",
        "stock_candles",
        [
            "symbol",
            "source_provider",
            "price_basis",
            "price_basis_rule_version",
            "data_stage",
            "interval",
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_stock_candles_price_basis_inventory", table_name="stock_candles")
    op.create_index(
        "ix_stock_candles_price_basis_inventory",
        "stock_candles",
        ["symbol", "source_provider", "price_basis", "data_stage", "interval"],
    )
    op.drop_column("stock_candles", "price_basis_rule_version")
