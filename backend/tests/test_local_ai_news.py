from datetime import datetime, timedelta, timezone
from dataclasses import replace
from decimal import Decimal

from app.local_ai.collection_universe import DEFAULT_COLLECTION_SYMBOLS
from app.local_ai.news_api import NEWS_ENTITY_TERMS, article_matches_symbol
from app.local_ai.news_features import (
    NEWS_FEATURES,
    build_news_training_rows,
    latest_news_features,
)
from app.providers.contracts import Candle


def test_news_entity_terms_cover_the_full_collection_universe():
    assert set(DEFAULT_COLLECTION_SYMBOLS) <= set(NEWS_ENTITY_TERMS)


def test_article_relevance_uses_company_names_instead_of_ambiguous_tickers():
    unrelated = {"title": "Analyst report: Weyerhaeuser Co", "description": ""}
    relevant = {"title": "Linde shares rise after earnings", "description": ""}

    assert article_matches_symbol("LIN", unrelated) is False
    assert article_matches_symbol("LIN", relevant) is True


def _articles(days: int = 30) -> list[dict]:
    start = datetime.now(timezone.utc) - timedelta(days=days)
    return [
        {
            "publishedAt": (start + timedelta(days=offset)).isoformat(),
            "title": "Company beats estimates with strong growth",
            "description": "Profit rises while risk declines",
            "source": {"name": f"Source {offset % 3}"},
            "url": f"https://example.test/{offset}",
        }
        for offset in range(days)
    ]


def _candles(days: int = 35) -> list[Candle]:
    start = datetime.now(timezone.utc) - timedelta(days=30)
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


def test_latest_news_features_are_bounded_and_complete():
    features = latest_news_features(_articles(5))

    assert set(features) == set(NEWS_FEATURES)
    assert features["positive_ratio"] > features["negative_ratio"]
    assert -1 <= features["sentiment_balance"] <= 1


def test_news_training_rows_use_future_price_return_label():
    rows = build_news_training_rows(_articles(), _candles(), horizon_days=3)

    assert len(rows) >= 20
    assert all(row["label"] == 1 for row in rows)
    assert all(row["future_return"] > 0 for row in rows)


def test_news_training_rows_can_exclude_ambiguous_returns():
    rows = build_news_training_rows(
        _articles(),
        _candles(),
        horizon_days=3,
        minimum_articles=2,
        minimum_absolute_excess_return=0.1,
    )

    assert rows == []


def test_news_training_rows_label_benchmark_underperformance():
    benchmark = _candles()
    benchmark = [
        replace(candle, close=candle.close + Decimal(index * 2))
        for index, candle in enumerate(benchmark)
    ]

    rows = build_news_training_rows(
        _articles(),
        _candles(),
        horizon_days=3,
        benchmark_candles=benchmark,
    )

    assert rows
    assert all(row["future_excess_return"] < 0 for row in rows)
    assert all(row["label"] == 0 for row in rows)
