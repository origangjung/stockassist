from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.local_ai.market_features import (
    LONG_HORIZON_RISK_FEATURES,
    build_market_training_rows,
)
from app.providers.contracts import Candle


def _candles(*, daily_step: int, days: int = 35) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        Candle(
            timestamp=start + timedelta(days=offset),
            open=Decimal(100 + daily_step * offset),
            high=Decimal(101 + daily_step * offset),
            low=Decimal(99 + daily_step * offset),
            close=Decimal(100 + daily_step * offset),
            volume=1000 + offset,
            price_basis="unadjusted",
        )
        for offset in range(days)
    ]


def test_market_labels_use_benchmark_relative_future_return():
    rows = build_market_training_rows(
        _candles(daily_step=1),
        benchmark_candles=_candles(daily_step=2),
        horizon_days=5,
    )

    assert rows
    assert all(row.future_return > 0 for row in rows)
    assert all(row.future_excess_return is not None for row in rows)
    assert all(row.future_excess_return < 0 for row in rows)
    assert all(row.technical_label == 0 for row in rows)
    assert all(row.future_max_drawdown < 0 for row in rows)


def test_long_horizon_risk_features_are_past_only_and_complete():
    rows = build_market_training_rows(
        _candles(daily_step=1, days=90),
        horizon_days=5,
        include_long_horizon_risk=True,
    )

    assert rows
    assert set(LONG_HORIZON_RISK_FEATURES).issubset(rows[0].risk)
    assert rows[0].risk["return_20d"] > 0
    assert rows[0].risk["volatility_ratio_20_60"] >= 0
