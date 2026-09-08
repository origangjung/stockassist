from datetime import datetime, timedelta, timezone
from dataclasses import replace
from decimal import Decimal

import pytest

from app.local_ai.flow_features import (
    FLOW_FEATURES,
    aggregate_short_volume,
    build_flow_training_rows,
    latest_flow_features,
    short_interest_features_by_date,
)
from app.providers.contracts import Candle


def _records(days: int = 30) -> list[dict]:
    start = datetime(2026, 1, 1).date()
    rows = []
    for offset in range(days):
        trade_date = (start + timedelta(days=offset)).isoformat()
        rows.extend(
            [
                {
                    "tradeReportDate": trade_date,
                    "shortParQuantity": 40 + offset,
                    "shortExemptParQuantity": 2,
                    "totalParQuantity": 100,
                },
                {
                    "tradeReportDate": trade_date,
                    "shortParQuantity": 20,
                    "shortExemptParQuantity": 1,
                    "totalParQuantity": 50,
                },
            ]
        )
    return rows


def _candles(days: int = 30) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        Candle(
            timestamp=start + timedelta(days=offset),
            open=Decimal(100 + offset),
            high=Decimal(102 + offset),
            low=Decimal(99 + offset),
            close=Decimal(101 + offset),
            volume=1000 + offset,
            price_basis="unadjusted",
        )
        for offset in range(days)
    ]


def test_aggregate_short_volume_combines_reporting_facilities():
    daily = aggregate_short_volume(_records(1))

    assert len(daily) == 1
    assert daily[0].short_quantity == 60
    assert daily[0].short_exempt_quantity == 3
    assert daily[0].total_quantity == 150


def test_flow_features_and_labels_are_complete():
    features = latest_flow_features(_records())
    rows = build_flow_training_rows(_records(), _candles(), horizon_days=5)

    assert features is not None
    assert set(features) == set(FLOW_FEATURES)
    assert len(rows) == 6
    assert all(row["label"] == 0 for row in rows)
    assert all(row["future_return"] > 0 for row in rows)


def test_short_interest_features_wait_for_conservative_publication_delay():
    records = [
        {
            "settlementDate": "2026-01-15",
            "currentShortPositionQuantity": 120,
            "previousShortPositionQuantity": 100,
            "daysToCoverQuantity": 2.0,
        }
    ]

    values = short_interest_features_by_date(
        records, [datetime(2026, 1, 28).date(), datetime(2026, 1, 29).date()]
    )

    assert datetime(2026, 1, 28).date() not in values
    assert values[datetime(2026, 1, 29).date()]["short_interest_change"] == pytest.approx(0.2)


def test_flow_label_means_future_benchmark_underperformance():
    benchmark = _candles()
    benchmark = [
        replace(candle, close=candle.close + Decimal(index * 2))
        for index, candle in enumerate(benchmark)
    ]

    rows = build_flow_training_rows(
        _records(),
        _candles(),
        horizon_days=5,
        benchmark_candles=benchmark,
    )

    assert rows
    assert all(row["future_excess_return"] < 0 for row in rows)
    assert all(row["label"] == 1 for row in rows)
