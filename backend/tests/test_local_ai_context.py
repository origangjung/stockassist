import pytest

from app.local_ai.context_features import add_financial_trends, add_news_trends


def test_financial_trends_only_use_previous_symbol_row():
    rows = [
        {
            "timestamp": "2025-01-01",
            "symbol": "AAPL",
            "revenue_growth_yoy": "0.1",
            "net_income_growth_yoy": "0.2",
            "net_margin": "0.3",
            "debt_to_assets": "0.4",
        },
        {
            "timestamp": "2025-04-01",
            "symbol": "AAPL",
            "revenue_growth_yoy": "0.15",
            "net_income_growth_yoy": "0.1",
            "net_margin": "0.32",
            "debt_to_assets": "0.35",
        },
    ]

    result = add_financial_trends(rows)

    assert len(result) == 1
    assert result[0]["revenue_growth_acceleration"] == pytest.approx(0.05)
    assert result[0]["net_income_growth_acceleration"] == pytest.approx(-0.1)


def test_news_trends_use_current_and_past_windows_only():
    rows = [
        {
            "timestamp": f"2025-01-0{index}",
            "symbol": "AAPL",
            "sentiment_balance": str(value),
            "article_count_3d": str(index),
            "source_diversity": "0.5",
        }
        for index, value in enumerate((0.1, 0.2, 0.6), start=1)
    ]

    result = add_news_trends(rows)

    assert len(result) == 2
    assert result[-1]["sentiment_change"] == pytest.approx(0.4)
    assert result[-1]["sentiment_mean_3"] == pytest.approx(0.3)
