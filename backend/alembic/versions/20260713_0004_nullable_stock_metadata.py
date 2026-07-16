"""Allow provider stock metadata that the upstream API does not supply."""

from alembic import op
import sqlalchemy as sa

revision = "20260713_0004"
down_revision = "20260713_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("stocks") as batch_op:
        batch_op.alter_column("sector", existing_type=sa.String(120), nullable=True)
        batch_op.alter_column("listed_at", existing_type=sa.DateTime(timezone=True), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("stocks") as batch_op:
        batch_op.alter_column("listed_at", existing_type=sa.DateTime(timezone=True), nullable=False)
        batch_op.alter_column("sector", existing_type=sa.String(120), nullable=False)
