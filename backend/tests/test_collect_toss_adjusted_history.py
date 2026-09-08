from datetime import datetime, timezone
from decimal import Decimal

from app.providers.contracts import Candle
from scripts.ai.data.collect_toss_adjusted_history import RequiredRange, required_ranges, validated_history


def _candle(day: int, *, basis: str = "provider_adjusted") -> Candle:
    return Candle(
        datetime(2024, 1, day, tzinfo=timezone.utc),
        Decimal("10"),
        Decimal("11"),
        Decimal("9"),
        Decimal("10"),
        100,
        basis,
    )


def test_required_ranges_prefer_original_feature_timestamp():
    ranges = required_ranges(
        [
            {
                "timestamp": "2025-01-10",
                "feature_timestamp": "2024-01-02",
                "symbol": "aapl",
            },
            {
                "timestamp": "2025-01-11",
                "feature_timestamp": "2024-01-08",
                "symbol": "AAPL",
            },
        ]
    )

    assert ranges["AAPL"] == RequiredRange(
        datetime(2024, 1, 2).date(), datetime(2024, 1, 8).date()
    )


def test_history_requires_verified_adjusted_unique_full_coverage():
    required = RequiredRange(datetime(2024, 1, 2).date(), datetime(2024, 1, 3).date())

    assert validated_history([_candle(1), _candle(2), _candle(3)], required)
    assert validated_history([_candle(2), _candle(3)], required) is None
    assert validated_history([_candle(1), _candle(2, basis="unknown"), _candle(3)], required) is None
    assert validated_history([_candle(1), _candle(2), _candle(2), _candle(3)], required) is None
