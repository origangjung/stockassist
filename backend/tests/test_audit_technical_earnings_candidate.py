from datetime import date, timedelta

from scripts.ai.training.audit_technical_earnings_candidate import audit


def _row(day: str, symbol: str = "AAPL") -> dict[str, str]:
    return {
        "timestamp": f"{day}T13:00:00+09:00",
        "symbol": symbol,
        "future_excess_return": "0.02",
        "horizon_days": "10",
        "earnings_available_date": day,
        "eps_surprise_signed_log": "0.1",
        "eps_surprise_positive": "1",
        "eps_yoy_growth_signed_log": "0.1",
        "eps_yoy_available": "1",
        "eps_beat_streak_scaled": "0.5",
        "earnings_age_log_scaled": "0",
        "earnings_event_3d": "1",
        "earnings_event_10d": "1",
    }


def test_earnings_audit_reports_small_candidate_without_failing():
    report = audit([_row("2026-01-02")], [{}, {}, {}, {}, {}])

    assert report["status"] == "collect_more_data"
    assert report["coverage"] == 0.2
    assert "timestamps_below_500" in report["reasons"]
    assert report["future_leakage_rows"] == 0


def test_earnings_audit_blocks_future_and_duplicate_rows():
    first = _row("2026-01-02")
    first["earnings_available_date"] = "2026-01-03"

    report = audit([first, dict(first)], [first, first])

    assert report["future_leakage_rows"] == 2
    assert report["duplicate_rows"] == 1
    assert "future_earnings_leakage" in report["reasons"]
    assert "duplicate_rows" in report["reasons"]


def test_earnings_audit_rejects_wrong_horizon_and_nonfinite_features():
    wrong_horizon = _row("2026-01-02")
    wrong_horizon["horizon_days"] = "5"
    nonfinite = _row("2026-01-03")
    nonfinite["eps_surprise_signed_log"] = "nan"

    report = audit([wrong_horizon, nonfinite], [wrong_horizon, nonfinite])

    assert report["invalid_rows"] == 2
    assert "invalid_rows" in report["reasons"]


def test_earnings_audit_opens_validation_only_after_all_thresholds_pass():
    start = date(2024, 1, 1)
    rows = [
        _row(
            (start + timedelta(days=day_index)).isoformat(),
            f"S{symbol_index:02d}",
        )
        for day_index in range(500)
        for symbol_index in range(20)
    ]

    report = audit(rows, rows)

    assert report["status"] == "ready_for_validation"
    assert report["rows"] == 10_000
    assert report["unique_timestamps"] == 500
    assert report["symbols"] == 20
    assert report["reasons"] == []
