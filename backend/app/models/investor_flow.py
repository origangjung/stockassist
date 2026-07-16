from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class InvestorFlowModel(Base):
    __tablename__ = "stock_investor_flows"
    __table_args__ = (
        UniqueConstraint("symbol", "as_of_date", "source", name="uq_investor_flow_snapshot"),
        Index("ix_investor_flows_symbol_date", "symbol", "as_of_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    foreign_net_quantity: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    institution_net_quantity: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    individual_net_quantity: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    foreign_holding_quantity: Mapped[Decimal | None] = mapped_column(Numeric(24, 6), nullable=True)
    foreign_holding_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    data_as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
