"""Add currency to the stock master for multi-market support."""

from alembic import op
import sqlalchemy as sa

revision = "20260713_0007"
down_revision = "20260713_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "stocks",
        sa.Column("currency", sa.String(8), nullable=False, server_default="KRW"),
    )


def downgrade() -> None:
    op.drop_column("stocks", "currency")
