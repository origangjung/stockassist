from scripts.ai.data.enrich_financial_earnings_expectations import enrich_rows


def test_expectations_join_uses_only_records_available_by_the_financial_date():
    financial = [
        {"timestamp": "2026-04-24", "symbol": "AAPL", "label": "1"},
        {"timestamp": "2026-04-27", "symbol": "AAPL", "label": "0"},
    ]
    earnings = [
        {
            "symbol": "AAPL",
            "fiscal_date": "2026-03-31",
            "reported_date": "2026-04-24",
            "available_date": "2026-04-27",
            "reported_eps": "1.2",
            "estimated_eps": "1.0",
            "eps_surprise": "0.2",
            "eps_surprise_percentage": "20.0",
            "report_time": "post-market",
        }
    ]

    rows, report = enrich_rows(financial, earnings)

    assert len(rows) == 1
    assert rows[0]["timestamp"] == "2026-04-27"
    assert rows[0]["eps_surprise_positive"] == 1.0
    assert report["missing_prior_earnings"] == 1


def test_expectations_features_use_only_prior_quarters_for_yoy_and_streak():
    earnings = []
    for index, year_quarter in enumerate(
        ("2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31", "2026-03-31")
    ):
        earnings.append(
            {
                "symbol": "AAPL",
                "fiscal_date": year_quarter,
                "reported_date": year_quarter,
                "available_date": year_quarter,
                "reported_eps": str(1 + index * 0.1),
                "estimated_eps": "1.0",
                "eps_surprise": "0.1",
                "eps_surprise_percentage": "10.0",
                "report_time": "pre-market",
            }
        )

    rows, _report = enrich_rows(
        [{"timestamp": "2026-04-01", "symbol": "AAPL", "label": "1"}],
        earnings,
    )

    assert rows[0]["eps_yoy_available"] == 1.0
    assert rows[0]["eps_yoy_growth_signed_log"] > 0
    assert rows[0]["eps_beat_streak_scaled"] == 1.0
