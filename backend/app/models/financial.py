from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CompanyModel(Base):
    __tablename__ = "companies"

    symbol: Mapped[str] = mapped_column(String(16), primary_key=True)
    dart_corp_code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class FinancialModel(Base):
    __tablename__ = "financials"
    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "fiscal_year",
            "report_code",
            "statement_type",
            name="uq_financial_snapshot",
        ),
        Index("ix_financials_symbol_year", "symbol", "fiscal_year"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    corp_code: Mapped[str] = mapped_column(String(8), nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    report_code: Mapped[str] = mapped_column(String(5), nullable=False)
    statement_type: Mapped[str] = mapped_column(String(3), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    revenue: Mapped[Decimal | None] = mapped_column(Numeric(30, 2), nullable=True)
    operating_income: Mapped[Decimal | None] = mapped_column(Numeric(30, 2), nullable=True)
    net_income: Mapped[Decimal | None] = mapped_column(Numeric(30, 2), nullable=True)
    total_assets: Mapped[Decimal | None] = mapped_column(Numeric(30, 2), nullable=True)
    total_liabilities: Mapped[Decimal | None] = mapped_column(Numeric(30, 2), nullable=True)
    total_equity: Mapped[Decimal | None] = mapped_column(Numeric(30, 2), nullable=True)
    data_as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
