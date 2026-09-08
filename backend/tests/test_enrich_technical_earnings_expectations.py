import pytest

from scripts.ai.data.enrich_technical_earnings_expectations import (
    enrich_technical_rows,
)


def _earnings(available_date: str, surprise: str) -> dict[str, str]:
    return {
        "symbol": "AAPL",
        "fiscal_date": available_date,
        "reported_date": available_date,
        "available_date": available_date,
        "reported_eps": "1.2",
        "estimated_eps": "1.0",
        "eps_surprise": "0.2",
        "eps_surprise_percentage": surprise,
        "report_time": "pre_market",
        "retrieved_date": "2026-08-30",
    }


def test_technical_earnings_join_uses_only_already_available_report():
    technical = [
        {"timestamp": "2026-04-30T13:00:00+09:00", "symbol": "AAPL"},
        {"timestamp": "2026-05-01T13:00:00+09:00", "symbol": "AAPL"},
        {"timestamp": "2026-05-04T13:00:00+09:00", "symbol": "AAPL"},
    ]

    rows, report = enrich_technical_rows(
        technical,
        [_earnings("2026-05-01", "20.0"), _earnings("2026-08-01", "-10.0")],
    )

    assert [row["timestamp"] for row in rows] == [
        "2026-05-01T13:00:00+09:00",
        "2026-05-04T13:00:00+09:00",
    ]
    assert all(row["eps_surprise_positive"] == 1.0 for row in rows)
    assert rows[0]["earnings_event_3d"] == 1.0
    assert rows[1]["earnings_event_3d"] == 1.0
    assert report["missing_prior_earnings"] == 1
    assert report["event_rows_10d"] == 2


def test_technical_earnings_join_marks_older_reports_outside_event_window():
    rows, _ = enrich_technical_rows(
        [{"timestamp": "2026-05-20", "symbol": "AAPL"}],
        [_earnings("2026-05-01", "20.0")],
    )

    assert rows[0]["earnings_event_3d"] == 0.0
    assert rows[0]["earnings_event_10d"] == 0.0
    assert 0 < rows[0]["earnings_age_log_scaled"] < 1


def test_technical_earnings_join_rejects_invalid_dates():
    with pytest.raises(ValueError):
        enrich_technical_rows(
            [{"timestamp": "not-a-date", "symbol": "AAPL"}],
            [_earnings("2026-05-01", "20.0")],
        )
