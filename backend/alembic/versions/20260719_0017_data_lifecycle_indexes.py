"""Add indexes used by operational data retention cleanup."""

from alembic import op

revision = "20260719_0017"
down_revision = "20260716_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_data_quality_logs_created_at",
        "data_quality_logs",
        ["created_at"],
    )
    op.create_index("ix_news_created_at", "news", ["created_at"])
    op.create_index("ix_disclosures_created_at", "disclosures", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_disclosures_created_at", table_name="disclosures")
    op.drop_index("ix_news_created_at", table_name="news")
    op.drop_index("ix_data_quality_logs_created_at", table_name="data_quality_logs")
