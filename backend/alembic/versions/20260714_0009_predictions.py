"""Create model registry metadata and prediction snapshots."""

from alembic import op
import sqlalchemy as sa

revision = "20260714_0009"
down_revision = "20260713_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_versions",
        sa.Column("version", sa.String(64), primary_key=True),
        sa.Column("algorithm", sa.String(32), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        sa.Column("validation_status", sa.String(24), nullable=False),
        sa.Column("validation_metrics", sa.JSON(), nullable=False),
        sa.Column("data_as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(16), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        sa.Column("rise_probability", sa.Numeric(10, 6), nullable=False),
        sa.Column("confidence_lower", sa.Numeric(10, 6), nullable=False),
        sa.Column("confidence_upper", sa.Numeric(10, 6), nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("validation_status", sa.String(24), nullable=False),
        sa.Column("data_as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_predictions_symbol", "predictions", ["symbol"])
    op.create_index("ix_predictions_model_version", "predictions", ["model_version"])


def downgrade() -> None:
    op.drop_index("ix_predictions_model_version", table_name="predictions")
    op.drop_index("ix_predictions_symbol", table_name="predictions")
    op.drop_table("predictions")
    op.drop_table("model_versions")
