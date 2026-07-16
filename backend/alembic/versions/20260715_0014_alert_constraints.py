"""Add data-integrity constraints for reference price alerts."""

from alembic import op

revision = "20260715_0014"
down_revision = "20260715_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("alerts") as batch_op:
        batch_op.create_check_constraint(
            "ck_alerts_condition",
            "condition IN ('above', 'below')",
        )
        batch_op.create_check_constraint(
            "ck_alerts_status",
            "status IN ('active', 'triggered', 'disabled')",
        )
        batch_op.create_check_constraint(
            "ck_alerts_target_price_positive",
            "target_price > 0",
        )


def downgrade() -> None:
    with op.batch_alter_table("alerts") as batch_op:
        batch_op.drop_constraint("ck_alerts_target_price_positive", type_="check")
        batch_op.drop_constraint("ck_alerts_status", type_="check")
        batch_op.drop_constraint("ck_alerts_condition", type_="check")
