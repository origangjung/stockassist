"""Add privacy-minimized external provider audit logs."""

from alembic import op
import sqlalchemy as sa

revision = "20260716_0016"
down_revision = "20260715_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provider_audit_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("method", sa.String(8), nullable=False),
        sa.Column("endpoint", sa.String(255), nullable=False),
        sa.Column("api_group", sa.String(64), nullable=False),
        sa.Column("outcome", sa.String(24), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(128), nullable=True),
        sa.Column("provider_request_id", sa.String(128), nullable=True),
        sa.Column("internal_request_id", sa.String(128), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "outcome IN ('success', 'error', 'transport_error')",
            name="ck_provider_audit_outcome",
        ),
        sa.CheckConstraint("attempt_count > 0", name="ck_provider_audit_attempt_count"),
        sa.CheckConstraint("duration_ms >= 0", name="ck_provider_audit_duration"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_provider_audit_provider_occurred",
        "provider_audit_logs",
        ["provider", "occurred_at"],
    )
    op.create_index(
        "ix_provider_audit_request_id",
        "provider_audit_logs",
        ["provider_request_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_provider_audit_request_id", table_name="provider_audit_logs")
    op.drop_index("ix_provider_audit_provider_occurred", table_name="provider_audit_logs")
    op.drop_table("provider_audit_logs")
