"""Record candle provider provenance without relabelling legacy price bases."""

from alembic import op
import sqlalchemy as sa

revision = "20260720_0020"
down_revision = "20260720_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "stock_candles",
        sa.Column(
            "source_provider",
            sa.String(32),
            nullable=False,
            server_default="legacy_unknown",
        ),
    )
    op.create_index(
        "ix_stock_candles_price_basis_inventory",
        "stock_candles",
        ["symbol", "source_provider", "price_basis", "data_stage", "interval"],
    )


def downgrade() -> None:
    op.drop_index("ix_stock_candles_price_basis_inventory", table_name="stock_candles")
    op.drop_column("stock_candles", "source_provider")
