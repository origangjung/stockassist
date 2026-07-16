from datetime import datetime
from decimal import Decimal

import pandas as pd

from app.backtest.strategies import Strategy
from app.indicators import IndicatorEngine
from app.providers.contracts import Candle
from app.score.engine import ScoreEngine, TechnicalScoreCalculator


class TechnicalScoreStrategy(Strategy):
    """Historical score threshold strategy for validation through BacktestEngine."""

    def __init__(self, threshold: float = 65):
        if not 0 <= threshold <= 100:
            raise ValueError("threshold must be between 0 and 100")
        self.threshold = threshold
        self.name = f"technical_score_{threshold:g}"
        self._indicators = IndicatorEngine()
        self._technical = TechnicalScoreCalculator()
        self._score = ScoreEngine()

    def signals(self, frame: pd.DataFrame) -> pd.Series:
        candles = [
            Candle(
                timestamp=value.timestamp
                if isinstance(value.timestamp, datetime)
                else pd.Timestamp(value.timestamp).to_pydatetime(),
                open=Decimal(str(value.open)),
                high=Decimal(str(value.high)),
                low=Decimal(str(value.low)),
                close=Decimal(str(value.close)),
                volume=int(value.volume),
            )
            for value in frame.itertuples(index=False)
        ]
        indicator_rows = self._indicators.calculate(candles)
        scores = [
            self._score.aggregate(self._technical.calculate(candle, row)).overall_score
            for candle, row in zip(candles, indicator_rows, strict=True)
        ]
        return pd.Series(
            [int(score >= self.threshold) for score in scores], index=frame.index, dtype="int64"
        )
