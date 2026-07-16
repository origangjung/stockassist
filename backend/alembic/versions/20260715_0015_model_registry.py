"""Add per-symbol Champion-Challenger model registry metadata."""

from alembic import op
import sqlalchemy as sa

revision = "20260715_0015"
down_revision = "20260715_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("model_versions", sa.Column("scope_symbol", sa.String(16), nullable=True))
    op.add_column(
        "model_versions",
        sa.Column(
            "registry_stage",
            sa.String(16),
            nullable=False,
            server_default="challenger",
        ),
    )
    op.add_column(
        "model_versions",
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        """
        UPDATE model_versions
        SET scope_symbol = COALESCE(
            (SELECT MIN(predictions.symbol)
             FROM predictions
             WHERE predictions.model_version = model_versions.version),
            'UNKNOWN'
        )
        """
    )
    with op.batch_alter_table("model_versions") as batch_op:
        batch_op.alter_column("scope_symbol", existing_type=sa.String(16), nullable=False)
    op.create_index(
        "ix_model_versions_scope_symbol",
        "model_versions",
        ["scope_symbol"],
    )
    op.create_index(
        "uq_model_versions_champion_scope",
        "model_versions",
        ["scope_symbol", "algorithm", "horizon_days"],
        unique=True,
        postgresql_where=sa.text("registry_stage = 'champion'"),
        sqlite_where=sa.text("registry_stage = 'champion'"),
    )


def downgrade() -> None:
    op.drop_index("uq_model_versions_champion_scope", table_name="model_versions")
    op.drop_index("ix_model_versions_scope_symbol", table_name="model_versions")
    with op.batch_alter_table("model_versions") as batch_op:
        batch_op.drop_column("promoted_at")
        batch_op.drop_column("registry_stage")
        batch_op.drop_column("scope_symbol")
