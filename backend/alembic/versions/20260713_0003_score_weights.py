"""Create versioned score weights."""

from alembic import op
import sqlalchemy as sa

revision = "20260713_0003"
down_revision = "20260713_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    table = op.create_table(
        "score_weights",
        sa.Column("version", sa.String(40), primary_key=True),
        sa.Column("weights", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_score_weights_is_active", "score_weights", ["is_active"])
    op.bulk_insert(
        table,
        [
            {
                "version": "weights-2026.1",
                "weights": {
                    "technical": 0.30,
                    "financial": 0.20,
                    "news": 0.10,
                    "disclosure": 0.10,
                    "investor_flow": 0.15,
                    "market_risk": 0.15,
                },
                "is_active": True,
            }
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_score_weights_is_active", table_name="score_weights")
    op.drop_table("score_weights")
