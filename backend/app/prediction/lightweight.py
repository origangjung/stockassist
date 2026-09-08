"""lightweight 파일은 백엔드 도메인 기능을 담당한다."""

from datetime import timezone
from decimal import Decimal
from hashlib import sha256
from math import exp, sqrt

import numpy as np

from app.prediction.contracts import PredictionResult
from app.providers.contracts import Candle


class LightweightPredictionEngine:
    """Small deterministic baseline for local previews without ML packages."""

    algorithm = "lightweight_momentum"

    def predict(self, symbol: str, candles: list[Candle], *, horizon_days: int) -> PredictionResult:
        """`predict`은(는) 입력 데이터를 기준으로 모델 또는 규칙의 결과 값을 계산해 반환합니다."""

        ordered = sorted(candles, key=lambda candle: candle.timestamp)
        if len(ordered) < 30:
            raise ValueError("at least 30 candles are required for lightweight prediction")
        closes = np.asarray([float(candle.close) for candle in ordered], dtype="float64")
        if np.any(closes <= 0):
            raise ValueError("candle closes must be positive")

        log_returns = np.diff(np.log(closes))
        window = log_returns[-min(20, len(log_returns)) :]
        momentum = float(window.mean()) * horizon_days
        volatility = float(window.std(ddof=1)) * sqrt(horizon_days)
        score = momentum / max(volatility, 1e-6)
        probability = 1.0 / (1.0 + exp(-max(-6.0, min(6.0, score))))
        uncertainty = min(0.25, max(0.08, 1.0 / sqrt(len(window))))

        fingerprint = sha256()
        fingerprint.update(closes.tobytes())
        fingerprint.update(f"{symbol.upper()}|{horizon_days}".encode())
        return PredictionResult(
            symbol=symbol,
            horizon_days=horizon_days,
            rise_probability=_decimal(probability),
            confidence_lower=_decimal(max(0.0, probability - uncertainty)),
            confidence_upper=_decimal(min(1.0, probability + uncertainty)),
            model_version=f"light-{fingerprint.hexdigest()[:12]}",
            validation_metrics={
                "observations": float(len(window)),
                "folds": 0.0,
            },
            validation_status="experimental",
            data_as_of=ordered[-1].timestamp.astimezone(timezone.utc),
        )


def _decimal(value: float) -> Decimal:
    """`_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return Decimal(str(round(value, 6)))
