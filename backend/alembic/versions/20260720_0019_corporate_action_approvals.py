"""Add immutable manual corporate action approval evidence."""

from alembic import op
import sqlalchemy as sa

revision = "20260720_0019"
down_revision = "20260719_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "corporate_action_approvals",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("corporate_action_id", sa.BigInteger(), nullable=False),
        sa.Column("group_hint", sa.String(64), nullable=False),
        sa.Column("receipt_no", sa.String(14), nullable=False),
        sa.Column("filing_evidence_url", sa.Text(), nullable=False),
        sa.Column("exchange_evidence_url", sa.Text(), nullable=False),
        sa.Column("reviewed_by", sa.String(64), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["corporate_action_id"], ["corporate_actions.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("corporate_action_id", name="uq_corporate_action_approval_action"),
        sa.UniqueConstraint("evidence_hash", name="uq_corporate_action_approval_evidence_hash"),
    )
    op.create_index(
        "ix_corporate_action_approvals_reviewed_at",
        "corporate_action_approvals",
        ["reviewed_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_corporate_action_approvals_reviewed_at",
        table_name="corporate_action_approvals",
    )
    op.drop_table("corporate_action_approvals")
