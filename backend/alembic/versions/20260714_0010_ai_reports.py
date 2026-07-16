"""Create auditable AI report history."""

from alembic import op
import sqlalchemy as sa

revision = "20260714_0010"
down_revision = "20260714_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_reports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(16), nullable=False),
        sa.Column("generator", sa.String(24), nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("validation_status", sa.String(24), nullable=False),
        sa.Column("data_as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("report", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_ai_reports_symbol", "ai_reports", ["symbol"])
    op.create_index("ix_ai_reports_model_version", "ai_reports", ["model_version"])


def downgrade() -> None:
    op.drop_index("ix_ai_reports_model_version", table_name="ai_reports")
    op.drop_index("ix_ai_reports_symbol", table_name="ai_reports")
    op.drop_table("ai_reports")
