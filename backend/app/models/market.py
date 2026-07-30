from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
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


class StockModel(Base):
    __tablename__ = "stocks"

    symbol: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    market: Mapped[str] = mapped_column(String(20), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="KRW")
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True)
    listed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class StockCandleModel(Base):
    __tablename__ = "stock_candles"
    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "timestamp",
            "interval",
            "data_stage",
            "aggregation_version",
            name="uq_stock_candle_identity",
        ),
        Index("ix_stock_candles_lookup", "symbol", "interval", "data_stage", "timestamp"),
        Index(
            "ix_stock_candles_price_basis_inventory",
            "symbol",
            "source_provider",
            "price_basis",
            "price_basis_rule_version",
            "data_stage",
            "interval",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    symbol: Mapped[str] = mapped_column(ForeignKey("stocks.symbol"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    interval: Mapped[str] = mapped_column(String(8), nullable=False, default="1d")
    data_stage: Mapped[str] = mapped_column(String(12), nullable=False)
    aggregation_version: Mapped[str] = mapped_column(String(24), nullable=False, default="raw")
    price_basis: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unknown", server_default="unknown"
    )
    source_provider: Mapped[str] = mapped_column(
        String(32), nullable=False, default="legacy_unknown", server_default="legacy_unknown"
    )
    price_basis_rule_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="legacy_unknown", server_default="legacy_unknown"
    )
    open: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class DataQualityLogModel(Base):
    __tablename__ = "data_quality_logs"
    __table_args__ = (
        Index("ix_quality_logs_symbol_created", "symbol", "created_at"),
        Index("ix_data_quality_logs_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    rule: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
