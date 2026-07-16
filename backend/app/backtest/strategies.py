from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any

import pandas as pd

from app.patterns import PatternEngine
from app.providers.contracts import Candle


class Strategy(ABC):
    name: str

    @abstractmethod
    def signals(self, candles: pd.DataFrame) -> pd.Series:
        """Return the desired long-only position observed at each bar close."""


class BuyAndHoldStrategy(Strategy):
    name = "buy_and_hold"

    def signals(self, candles: pd.DataFrame) -> pd.Series:
        return pd.Series(1, index=candles.index, dtype="int64")


class MovingAverageCrossStrategy(Strategy):
    def __init__(self, fast_period: int = 5, slow_period: int = 20):
        if fast_period <= 0 or slow_period <= 0 or fast_period >= slow_period:
            raise ValueError("periods must satisfy 0 < fast_period < slow_period")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.name = f"ma_cross_{fast_period}_{slow_period}"

    def signals(self, candles: pd.DataFrame) -> pd.Series:
        fast = candles["close"].rolling(self.fast_period).mean()
        slow = candles["close"].rolling(self.slow_period).mean()
        return (fast > slow).fillna(False).astype("int64")


class PatternReferenceStrategy(Strategy):
    """Long-only experimental strategy driven by confirmed deterministic patterns."""

    name = "pattern_reference"

    def __init__(self, minimum_confidence: float = 0.68, window: int = 60) -> None:
        if not 0 <= minimum_confidence <= 1:
            raise ValueError("minimum_confidence must be between 0 and 1")
        if window < 21:
            raise ValueError("pattern window must be at least 21 candles")
        self.minimum_confidence = minimum_confidence
        self.window = window
        self._engine = PatternEngine()
        self._signatures: list[tuple[Any, ...]] = []
        self._signals: list[int] = []

    def signals(self, candles: pd.DataFrame) -> pd.Series:
        signatures = [self._signature(row) for row in candles.itertuples(index=False)]
        common = 0
        while (
            common < len(signatures)
            and common < len(self._signatures)
            and signatures[common] == self._signatures[common]
        ):
            common += 1
        self._signatures = self._signatures[:common]
        self._signals = self._signals[:common]
        desired_position = self._signals[-1] if self._signals else 0

        for index in range(common, len(candles)):
            start = max(0, index - self.window + 1)
            window = self._to_candles(candles.iloc[start : index + 1])
            patterns = self._engine.analyze(window)["patterns"]
            directional = [
                pattern
                for pattern in patterns
                if pattern["direction"] in {"upward", "downward"}
                and pattern["confidence"] >= self.minimum_confidence
            ]
            if directional:
                desired_position = 1 if directional[0]["direction"] == "upward" else 0
            self._signals.append(desired_position)
            self._signatures.append(signatures[index])
        return pd.Series(self._signals, index=candles.index, dtype="int64")

    @staticmethod
    def _signature(row: Any) -> tuple[Any, ...]:
        return (
            row.timestamp,
            row.open,
            row.high,
            row.low,
            row.close,
            row.volume,
        )

    @staticmethod
    def _to_candles(frame: pd.DataFrame) -> list[Candle]:
        converted: list[Candle] = []
        for row in frame.itertuples(index=False):
            timestamp = row.timestamp
            if isinstance(timestamp, pd.Timestamp):
                timestamp = timestamp.to_pydatetime()
            converted.append(
                Candle(
                    timestamp=timestamp,
                    open=Decimal(str(row.open)),
                    high=Decimal(str(row.high)),
                    low=Decimal(str(row.low)),
                    close=Decimal(str(row.close)),
                    volume=int(row.volume),
                )
            )
        return converted
