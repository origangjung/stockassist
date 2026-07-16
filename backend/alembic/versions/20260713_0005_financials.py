"""Create DART company and normalized financial snapshot tables."""

from alembic import op
import sqlalchemy as sa

revision = "20260713_0005"
down_revision = "20260713_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("symbol", sa.String(16), primary_key=True),
        sa.Column("dart_corp_code", sa.String(8), nullable=False, unique=True),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_table(
        "financials",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(16), nullable=False),
        sa.Column("corp_code", sa.String(8), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("report_code", sa.String(5), nullable=False),
        sa.Column("statement_type", sa.String(3), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("revenue", sa.Numeric(30, 2), nullable=True),
        sa.Column("operating_income", sa.Numeric(30, 2), nullable=True),
        sa.Column("net_income", sa.Numeric(30, 2), nullable=True),
        sa.Column("total_assets", sa.Numeric(30, 2), nullable=True),
        sa.Column("total_liabilities", sa.Numeric(30, 2), nullable=True),
        sa.Column("total_equity", sa.Numeric(30, 2), nullable=True),
        sa.Column("data_as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(24), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "symbol", "fiscal_year", "report_code", "statement_type", name="uq_financial_snapshot"
        ),
    )
    op.create_index("ix_financials_symbol_year", "financials", ["symbol", "fiscal_year"])


def downgrade() -> None:
    op.drop_index("ix_financials_symbol_year", table_name="financials")
    op.drop_table("financials")
    op.drop_table("companies")
