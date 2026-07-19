from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DisclosureModel(Base):
    __tablename__ = "disclosures"
    __table_args__ = (
        Index("ix_disclosures_symbol_filed_at", "symbol", "filed_at"),
        Index("ix_disclosures_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    corp_code: Mapped[str] = mapped_column(String(8), nullable=False)
    receipt_no: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(160), nullable=False)
    report_name: Mapped[str] = mapped_column(String(500), nullable=False)
    filed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    filer_name: Mapped[str] = mapped_column(String(160), nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class NewsArticleModel(Base):
    __tablename__ = "news"
    __table_args__ = (
        Index("ix_news_symbol_published_at", "symbol", "published_at"),
        Index("ix_news_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    publisher: Mapped[str] = mapped_column(String(160), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
