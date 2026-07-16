from datetime import datetime, timezone
from decimal import Decimal

from app.pipeline.candles import CandleInterval, CandlePipeline, QualitySeverity
from app.providers.contracts import Candle


def candle(day: int, close: str, volume: int = 100) -> Candle:
    price = Decimal(close)
    return Candle(
        datetime(2026, 7, day, tzinfo=timezone.utc), price, price + 2, price - 2, price, volume
    )


def test_pipeline_removes_invalid_candles_and_records_quality_log():
    invalid = Candle(
        datetime(2026, 7, 2, tzinfo=timezone.utc),
        Decimal("10"),
        Decimal("9"),
        Decimal("8"),
        Decimal("10"),
        1,
    )
    result = CandlePipeline().process([candle(1, "10"), invalid])
    assert len(result.cleaned_candles) == 1
    assert any(log.severity == QualitySeverity.ERROR for log in result.quality_logs)


def test_weekly_aggregation_preserves_ohlcv_boundaries():
    result = CandlePipeline().process(
        [candle(6, "10", 10), candle(7, "12", 20), candle(8, "11", 30)], CandleInterval.WEEK
    )
    weekly = result.cleaned_candles[0]
    assert weekly.open == Decimal("10")
    assert weekly.close == Decimal("11")
    assert weekly.volume == 60


def test_daily_gap_detection_ignores_weekends_and_short_market_holidays():
    result = CandlePipeline().process(
        [
            candle(3, "10"),
            candle(6, "11"),
            candle(10, "12"),
        ]
    )

    assert not any(log.rule == "missing_daily_candles" for log in result.quality_logs)


def test_daily_gap_detection_warns_after_five_missing_business_days():
    result = CandlePipeline().process(
        [
            candle(1, "10"),
            candle(10, "12"),
        ]
    )

    gaps = [log for log in result.quality_logs if log.rule == "missing_daily_candles"]
    assert len(gaps) == 1
    assert gaps[0].severity == QualitySeverity.WARNING
    assert "6영업일" in gaps[0].message
    assert result.aggregation_version == "2026.2"


def test_gap_detection_sorts_timestamps_without_hiding_out_of_order_error():
    result = CandlePipeline().process([candle(10, "12"), candle(1, "10")])

    assert any(log.rule == "out_of_order" for log in result.quality_logs)
    assert any(log.rule == "missing_daily_candles" for log in result.quality_logs)
