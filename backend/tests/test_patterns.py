from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.patterns import PatternEngine
from app.providers.contracts import Candle


def candle(
    day: int,
    open_price: float,
    high: float,
    low: float,
    close: float,
) -> Candle:
    return Candle(
        datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=day),
        Decimal(str(open_price)),
        Decimal(str(high)),
        Decimal(str(low)),
        Decimal(str(close)),
        1_000,
    )


def names(result: dict) -> set[str]:
    return {pattern["name"] for pattern in result["patterns"]}


def test_detects_doji_and_hammer_without_future_candles():
    doji = PatternEngine().analyze([candle(0, 100, 105, 95, 100.5)])
    hammer = PatternEngine().analyze([candle(0, 104, 105, 90, 102)])

    assert "doji" in names(doji)
    assert "hammer" in names(hammer)
    assert hammer["data_as_of"] == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert hammer["validation_status"] == "experimental"


def test_detects_shooting_star():
    result = PatternEngine().analyze([candle(0, 96, 110, 95, 98)])

    assert "shooting_star" in names(result)


def test_detects_bullish_and_bearish_engulfing():
    bullish = PatternEngine().analyze([candle(0, 104, 105, 99, 100), candle(1, 99, 106, 98, 105)])
    bearish = PatternEngine().analyze([candle(0, 100, 105, 99, 104), candle(1, 105, 106, 98, 99)])

    assert "bullish_engulfing" in names(bullish)
    assert "bearish_engulfing" in names(bearish)


def test_detects_prior_twenty_candle_range_breakout():
    history = [candle(index, 100, 102, 98, 100) for index in range(20)]
    result = PatternEngine().analyze([*history, candle(20, 101, 106, 100, 105)])

    breakout = next(item for item in result["patterns"] if item["name"] == "range_breakout_up")
    assert breakout["direction"] == "upward"
    assert breakout["ended_at"] == datetime(2026, 1, 21, tzinfo=timezone.utc)

    downward = PatternEngine().analyze([*history, candle(20, 99, 100, 94, 95)])
    assert "range_breakout_down" in names(downward)


def test_detects_confirmed_double_top():
    highs = [100, 102, 105, 110, 105, 102, 100, 103, 106, 109.5, 106, 101, 98, 95]
    candles = [
        candle(index, high - 3, high, high - 6, high - 2) for index, high in enumerate(highs)
    ]
    result = PatternEngine().analyze(candles)

    assert "double_top_confirmed" in names(result)


def test_detects_confirmed_double_bottom():
    lows = [100, 98, 95, 90, 95, 98, 100, 97, 94, 90.5, 94, 99, 102, 105]
    candles = [candle(index, low + 3, low + 6, low, low + 2) for index, low in enumerate(lows)]
    result = PatternEngine().analyze(candles)

    assert "double_bottom_confirmed" in names(result)


def test_rejects_invalid_ohlc_input():
    with pytest.raises(ValueError, match="invalid OHLC"):
        PatternEngine().analyze([candle(0, 100, 99, 95, 98)])
