"""모의투자 계좌, 보유 종목, 체결 기록의 영속 모델이다."""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PaperAccountModel(Base):
    """개인정보 대신 브라우저가 생성한 UUID로 구분되는 모의 계좌다."""

    __tablename__ = "paper_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    initial_cash_krw: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    initial_cash_usd: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    cash_krw: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    cash_usd: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PaperPositionModel(Base):
    """종목별 수량과 평균단가를 저장하는 모의 보유 종목이다."""

    __tablename__ = "paper_positions"
    __table_args__ = (
        UniqueConstraint("account_id", "symbol", name="uq_paper_position_account_symbol"),
    )

    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("paper_accounts.id", ondelete="CASCADE"), primary_key=True
    )
    symbol: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    market: Mapped[str] = mapped_column(String(32), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    average_price: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    last_price: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class PaperOrderModel(Base):
    """중복 요청 방지 키를 포함하는 변경 불가능한 모의 체결 원장이다."""

    __tablename__ = "paper_orders"
    __table_args__ = (
        UniqueConstraint("account_id", "idempotency_key", name="uq_paper_order_idempotency"),
        Index("ix_paper_orders_account_executed", "account_id", "executed_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String(36), nullable=False)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    market: Mapped[str] = mapped_column(String(32), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    side: Mapped[str] = mapped_column(String(4), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    fill_price: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    notional: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    commission: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

