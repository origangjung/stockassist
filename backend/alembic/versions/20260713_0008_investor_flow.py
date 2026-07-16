"""Create investor-flow snapshots for domestic securities."""

from alembic import op
import sqlalchemy as sa

revision = "20260713_0008"
down_revision = "20260713_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_investor_flows",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(16), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("foreign_net_quantity", sa.Numeric(24, 6), nullable=False),
        sa.Column("institution_net_quantity", sa.Numeric(24, 6), nullable=False),
        sa.Column("individual_net_quantity", sa.Numeric(24, 6), nullable=False),
        sa.Column("foreign_holding_quantity", sa.Numeric(24, 6), nullable=True),
        sa.Column("foreign_holding_rate", sa.Numeric(10, 6), nullable=True),
        sa.Column("data_as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(24), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("symbol", "as_of_date", "source", name="uq_investor_flow_snapshot"),
    )
    op.create_index(
        "ix_investor_flows_symbol_date", "stock_investor_flows", ["symbol", "as_of_date"]
    )


def downgrade() -> None:
    op.drop_index("ix_investor_flows_symbol_date", table_name="stock_investor_flows")
    op.drop_table("stock_investor_flows")
