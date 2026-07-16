from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from app.providers.contracts import Candle


@dataclass(frozen=True)
class PredictionResult:
    symbol: str
    horizon_days: int
    rise_probability: Decimal
    confidence_lower: Decimal
    confidence_upper: Decimal
    model_version: str
    validation_metrics: dict[str, float]
    validation_status: str
    data_as_of: datetime


class PredictionEngine(Protocol):
    algorithm: str

    def predict(
        self,
        symbol: str,
        candles: list[Candle],
        *,
        horizon_days: int,
    ) -> PredictionResult: ...


@dataclass(frozen=True)
class ModelVersionRecord:
    version: str
    symbol: str
    algorithm: str
    horizon_days: int
    validation_status: str
    validation_metrics: dict[str, float]
    registry_stage: str
    data_as_of: datetime
    promoted_at: datetime | None = None
    created_at: datetime | None = None
