from scripts.ai.data.relabel_financial_sector_neutral import relabel


def _row(symbol, outcome, *, timestamp="2026-01-01T09:00:00", outcome_date="2026-01-02"):
    return {
        "timestamp": timestamp,
        "outcome_start_timestamp": outcome_date,
        "symbol": symbol,
        "revenue_growth_yoy": "0.1",
        "net_income_growth_yoy": "0.1",
        "net_margin": "0.1",
        "debt_to_assets": "0.4",
        "equity_to_assets": "0.6",
        "asset_growth_yoy": "0.05",
        "future_excess_return": str(outcome),
        "label": "0",
    }


def test_financial_relabel_uses_sector_date_median_and_equal_date_weight():
    rows = [
        _row("AAPL", 0.04),
        _row("MSFT", -0.02),
        _row("JPM", 0.03),
        _row("BAC", -0.01),
        _row("WMT", 0.01),
    ]

    labeled, report = relabel(
        rows,
        minimum_sector_peers=2,
        minimum_market_peers=5,
        minimum_absolute_return=0.0,
    )

    labels = {row["symbol"]: row["label"] for row in labeled}
    assert labels["AAPL"] == 1
    assert labels["MSFT"] == 0
    assert labels["JPM"] == 1
    assert labels["BAC"] == 0
    assert report["positive_rate"] == 0.4
    assert sum(float(row["sample_weight"]) for row in labeled) == len(labeled)


def test_financial_relabel_deduplicates_same_symbol_outcome_session():
    rows = [
        _row("AAPL", 0.04, timestamp="2026-01-01T08:00:00"),
        _row("AAPL", 0.04, timestamp="2026-01-01T10:00:00"),
        _row("MSFT", -0.02),
    ]

    labeled, report = relabel(
        rows,
        minimum_sector_peers=2,
        minimum_market_peers=5,
        minimum_absolute_return=0.0,
    )

    assert report["deduplicated_rows"] == 2
    assert len(labeled) == 2
    aapl = next(row for row in labeled if row["symbol"] == "AAPL")
    assert aapl["feature_timestamp"] == "2026-01-01T10:00:00"
