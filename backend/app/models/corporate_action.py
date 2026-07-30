from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CorporateActionModel(Base):
    __tablename__ = "corporate_actions"
    __table_args__ = (
        UniqueConstraint(
            "source",
            "symbol",
            "event_id",
            "revision",
            name="uq_corporate_action_revision",
        ),
        CheckConstraint(
            "action_type IN ('split', 'reverse_split', 'cash_dividend', "
            "'stock_dividend', 'rights_issue')",
            name="ck_corporate_action_type",
        ),
        CheckConstraint(
            "status IN ('announced', 'confirmed', 'cancelled')",
            name="ck_corporate_action_status",
        ),
        CheckConstraint("revision > 0", name="ck_corporate_action_revision"),
        CheckConstraint("price_factor > 0", name="ck_corporate_action_price_factor"),
        CheckConstraint("volume_factor > 0", name="ck_corporate_action_volume_factor"),
        Index("ix_corporate_actions_symbol_effective", "symbol", "effective_at"),
        Index("ix_corporate_actions_symbol_known", "symbol", "known_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    symbol: Mapped[str] = mapped_column(ForeignKey("stocks.symbol"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(24), nullable=False)
    event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    announced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    known_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price_factor: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False)
    volume_factor: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class CorporateActionApprovalModel(Base):
    __tablename__ = "corporate_action_approvals"
    __table_args__ = (
        UniqueConstraint("corporate_action_id", name="uq_corporate_action_approval_action"),
        UniqueConstraint("evidence_hash", name="uq_corporate_action_approval_evidence_hash"),
        Index("ix_corporate_action_approvals_reviewed_at", "reviewed_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    corporate_action_id: Mapped[int] = mapped_column(
        ForeignKey("corporate_actions.id", ondelete="RESTRICT"), nullable=False
    )
    group_hint: Mapped[str] = mapped_column(String(64), nullable=False)
    receipt_no: Mapped[str] = mapped_column(String(14), nullable=False)
    filing_evidence_url: Mapped[str] = mapped_column(Text, nullable=False)
    exchange_evidence_url: Mapped[str] = mapped_column(Text, nullable=False)
    reviewed_by: Mapped[str] = mapped_column(String(64), nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
