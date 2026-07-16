from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.indicators import IndicatorEngine
from app.providers.contracts import Candle


def rising_candles(count: int = 40) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        Candle(
            start + timedelta(days=i),
            Decimal(100 + i),
            Decimal(102 + i),
            Decimal(98 + i),
            Decimal(101 + i),
            100,
        )
        for i in range(count)
    ]


def test_golden_monotonic_series_indicators():
    result = IndicatorEngine().calculate(rising_candles())
    latest = result[-1]
    assert latest["ma_5"] == 138.0
    assert latest["ma_20"] == 130.5
    assert latest["rsi_14"] == 100.0
    assert latest["mfi_14"] == 100.0
    assert latest["obv"] == 3900.0
    assert latest["vwap"] == 119.833333


def test_warmup_periods_are_explicitly_null():
    result = IndicatorEngine().calculate(rising_candles(10))
    assert result[-1]["rsi_14"] is None
    assert result[-1]["ma_20"] is None
    assert result[-1]["atr_14"] is None
