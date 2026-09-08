"""add isolated paper trading ledger

Revision ID: 20260814_0022
Revises: 20260720_0021
"""

from alembic import op
import sqlalchemy as sa

revision = "20260814_0022"
down_revision = "20260720_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "paper_accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("initial_cash_krw", sa.Numeric(24, 2), nullable=False),
        sa.Column("initial_cash_usd", sa.Numeric(24, 2), nullable=False),
        sa.Column("cash_krw", sa.Numeric(24, 2), nullable=False),
        sa.Column("cash_usd", sa.Numeric(24, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "paper_positions",
        sa.Column("account_id", sa.String(36), sa.ForeignKey("paper_accounts.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("symbol", sa.String(16), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("market", sa.String(32), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("quantity", sa.Numeric(24, 6), nullable=False),
        sa.Column("average_price", sa.Numeric(24, 6), nullable=False),
        sa.Column("last_price", sa.Numeric(24, 6), nullable=False),
        sa.Column("realized_pnl", sa.Numeric(24, 2), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("account_id", "symbol", name="uq_paper_position_account_symbol"),
    )
    op.create_table(
        "paper_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("idempotency_key", sa.String(36), nullable=False),
        sa.Column("symbol", sa.String(16), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("market", sa.String(32), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("side", sa.String(4), nullable=False),
        sa.Column("quantity", sa.Numeric(24, 6), nullable=False),
        sa.Column("fill_price", sa.Numeric(24, 6), nullable=False),
        sa.Column("notional", sa.Numeric(24, 2), nullable=False),
        sa.Column("commission", sa.Numeric(24, 2), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("account_id", "idempotency_key", name="uq_paper_order_idempotency"),
    )
    op.create_index("ix_paper_orders_account_executed", "paper_orders", ["account_id", "executed_at"])


def downgrade() -> None:
    op.drop_index("ix_paper_orders_account_executed", table_name="paper_orders")
    op.drop_table("paper_orders")
    op.drop_table("paper_positions")
    op.drop_table("paper_accounts")

