from datetime import date

import pytest

from scripts.ai.data.collect_earnings_expectations import symbols_due


def test_earnings_collection_rotates_only_missing_or_stale_symbols():
    rows = [
        {"symbol": "AAPL", "retrieved_date": "2026-08-20"},
        {"symbol": "MSFT", "retrieved_date": "2026-07-01"},
    ]

    pending = symbols_due(
        ("AAPL", "MSFT", "NVDA"),
        rows,
        today=date(2026, 8, 30),
        refresh_days=21,
        force=False,
    )

    assert pending == ["MSFT", "NVDA"]


def test_earnings_collection_validates_refresh_period_and_force_mode():
    with pytest.raises(ValueError, match="refresh-days"):
        symbols_due(("AAPL",), [], today=date(2026, 8, 30), refresh_days=1, force=False)

    assert symbols_due(
        ("AAPL",),
        [{"symbol": "AAPL", "retrieved_date": "2026-08-30"}],
        today=date(2026, 8, 30),
        refresh_days=21,
        force=True,
    ) == ["AAPL"]
