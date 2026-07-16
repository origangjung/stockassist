"""Create normalized disclosure and news article tables."""

from alembic import op
import sqlalchemy as sa

revision = "20260713_0006"
down_revision = "20260713_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "disclosures",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(16), nullable=False),
        sa.Column("corp_code", sa.String(8), nullable=False),
        sa.Column("receipt_no", sa.String(24), nullable=False, unique=True),
        sa.Column("company_name", sa.String(160), nullable=False),
        sa.Column("report_name", sa.String(500), nullable=False),
        sa.Column("filed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("filer_name", sa.String(160), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("document_url", sa.String(500), nullable=False),
        sa.Column("source", sa.String(24), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_disclosures_symbol_filed_at", "disclosures", ["symbol", "filed_at"])
    op.create_table(
        "news",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(16), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False, unique=True),
        sa.Column("publisher", sa.String(160), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("source", sa.String(24), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_news_symbol_published_at", "news", ["symbol", "published_at"])


def downgrade() -> None:
    op.drop_index("ix_news_symbol_published_at", table_name="news")
    op.drop_table("news")
    op.drop_index("ix_disclosures_symbol_filed_at", table_name="disclosures")
    op.drop_table("disclosures")
