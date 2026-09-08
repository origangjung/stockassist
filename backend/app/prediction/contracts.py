"""contracts 파일은 백엔드 도메인 기능을 담당한다."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from app.providers.contracts import Candle


@dataclass(frozen=True)
class PredictionResult:
    """계산 또는 처리 결과를 묶어 전달하는 값 객체입니다."""

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
    """`PredictionEngine` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

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
    """저장하거나 전송할 한 건의 구조화된 데이터를 나타냅니다."""

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
