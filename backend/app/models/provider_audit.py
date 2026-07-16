from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ProviderAuditLogModel(Base):
    __tablename__ = "provider_audit_logs"
    __table_args__ = (
        Index("ix_provider_audit_provider_occurred", "provider", "occurred_at"),
        Index("ix_provider_audit_request_id", "provider_request_id"),
        CheckConstraint(
            "outcome IN ('success', 'error', 'transport_error')",
            name="ck_provider_audit_outcome",
        ),
        CheckConstraint("attempt_count > 0", name="ck_provider_audit_attempt_count"),
        CheckConstraint("duration_ms >= 0", name="ck_provider_audit_duration"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    method: Mapped[str] = mapped_column(String(8), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    api_group: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(String(24), nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    provider_request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    internal_request_id: Mapped[str] = mapped_column(String(128), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
