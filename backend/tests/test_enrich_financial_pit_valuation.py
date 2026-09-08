from datetime import date
import math

from app.local_ai.financial_features import AnnualValuationSnapshot
from scripts.ai.data.enrich_financial_pit_valuation import (
    build_price_index,
    enrich_roe_rows,
    enrich_rows,
)


def test_pit_valuation_uses_latest_public_annual_and_prior_close_only():
    rows = [
        {
            "timestamp": "2025-05-02T13:00:00+09:00",
            "feature_timestamp": "2025-05-01T10:00:00",
            "symbol": "AAPL",
            "label": "1",
        }
    ]
    annuals = {
        "AAPL": [
            AnnualValuationSnapshot(date(2024, 2, 1), "old", 1000, 100, 500, 10),
            AnnualValuationSnapshot(date(2025, 2, 1), "current", 1200, 120, 600, 12),
            AnnualValuationSnapshot(date(2025, 6, 1), "future", 9999, 999, 999, 99),
        ]
    }
    prices = build_price_index(
        [
            {"timestamp": "2025-04-30", "symbol": "AAPL", "close_price": "100"},
            {"timestamp": "2025-05-01", "symbol": "AAPL", "close_price": "500"},
        ]
    )

    enriched, report = enrich_rows(rows, annuals, prices)

    assert report["coverage"] == 1.0
    assert enriched[0]["valuation_filed"] == "2025-02-01"
    assert enriched[0]["valuation_price_timestamp"] == "2025-04-30"
    assert enriched[0]["pit_per"] == 10
    assert enriched[0]["pit_pbr"] == 2
    assert enriched[0]["pit_psr"] == 1
    assert enriched[0]["pit_roe"] == 0.2
    assert enriched[0]["pit_per_signed_log"] == math.log1p(10)


def test_pit_valuation_preserves_negative_earnings_signal():
    rows = [{"timestamp": "2025-03-02", "symbol": "LOSS", "label": "0"}]
    annuals = {
        "LOSS": [
            AnnualValuationSnapshot(date(2025, 2, 1), "loss", 1000, -50, 400, 10)
        ]
    }
    prices = build_price_index(
        [{"timestamp": "2025-02-28", "symbol": "LOSS", "close_price": "20"}]
    )

    enriched, _ = enrich_rows(rows, annuals, prices)

    assert enriched[0]["pit_per"] == -4
    assert enriched[0]["pit_per_signed_log"] == -math.log1p(4)
    assert enriched[0]["pit_roe"] == -0.125


def test_pit_valuation_rejects_same_day_price_without_prior_session():
    rows = [{"timestamp": "2025-03-02", "symbol": "AAPL", "label": "1"}]
    annuals = {
        "AAPL": [AnnualValuationSnapshot(date(2025, 2, 1), "a", 100, 10, 50, 5)]
    }
    prices = build_price_index(
        [{"timestamp": "2025-03-02", "symbol": "AAPL", "close_price": "20"}]
    )

    enriched, report = enrich_rows(rows, annuals, prices)

    assert enriched == []
    assert report["missing_price"] == 1


def test_pit_roe_enrichment_does_not_require_prices_or_shares():
    rows = [{"timestamp": "2025-03-02", "symbol": "AAPL", "label": "1"}]
    annuals = {
        "AAPL": [AnnualValuationSnapshot(date(2025, 2, 1), "a", 100, -10, 50, None)]
    }

    enriched, report = enrich_roe_rows(rows, annuals)

    assert report["coverage"] == 1.0
    assert enriched[0]["pit_roe"] == -0.2
    assert enriched[0]["pit_roe_signed_log"] == -math.log1p(0.2)
