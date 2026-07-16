from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class BrokerAccountModel(Base):
    __tablename__ = "broker_accounts"
    __table_args__ = (
        UniqueConstraint("provider", "account_seq", name="uq_broker_provider_account_seq"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(24), nullable=False)
    account_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    account_no_masked: Mapped[str] = mapped_column(String(24), nullable=False)
    account_type: Mapped[str] = mapped_column(String(48), nullable=False)
    sync_status: Mapped[str] = mapped_column(String(24), nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class HoldingModel(Base):
    __tablename__ = "holdings"
    __table_args__ = (
        UniqueConstraint(
            "provider", "account_seq", "symbol", name="uq_holding_provider_account_symbol"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(24), nullable=False)
    account_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    market_country: Mapped[str] = mapped_column(String(8), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    last_price: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    average_purchase_price: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    purchase_amount: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    market_value: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    market_value_after_cost: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    profit_loss: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    profit_loss_after_cost: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    profit_rate: Mapped[Decimal] = mapped_column(Numeric(12, 8), nullable=False)
    profit_rate_after_cost: Mapped[Decimal] = mapped_column(Numeric(12, 8), nullable=False)
    daily_profit_loss: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    daily_profit_rate: Mapped[Decimal] = mapped_column(Numeric(12, 8), nullable=False)
    commission: Mapped[Decimal | None] = mapped_column(Numeric(24, 6), nullable=True)
    tax: Mapped[Decimal | None] = mapped_column(Numeric(24, 6), nullable=True)
    data_as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
