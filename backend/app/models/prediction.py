from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Index, Integer, JSON, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ModelVersionModel(Base):
    __tablename__ = "model_versions"
    __table_args__ = (
        Index(
            "uq_model_versions_champion_scope",
            "scope_symbol",
            "algorithm",
            "horizon_days",
            unique=True,
            postgresql_where=text("registry_stage = 'champion'"),
            sqlite_where=text("registry_stage = 'champion'"),
        ),
    )

    version: Mapped[str] = mapped_column(String(64), primary_key=True)
    scope_symbol: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    algorithm: Mapped[str] = mapped_column(String(32), nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    validation_status: Mapped[str] = mapped_column(String(24), nullable=False)
    validation_metrics: Mapped[dict] = mapped_column(JSON, nullable=False)
    registry_stage: Mapped[str] = mapped_column(String(16), nullable=False, default="challenger")
    data_as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class PredictionModel(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    rise_probability: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    confidence_lower: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    confidence_upper: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    validation_status: Mapped[str] = mapped_column(String(24), nullable=False)
    data_as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
