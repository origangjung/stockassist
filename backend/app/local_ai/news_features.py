"""news_features 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import math
import re

from app.providers.contracts import Candle


NEWS_FEATURES = (
    "article_count_3d",
    "positive_ratio",
    "negative_ratio",
    "sentiment_balance",
    "source_diversity",
    "average_title_length",
)

_POSITIVE = frozenset(
    {
        "beat", "beats", "bullish", "gain", "gains", "growth", "higher", "improve",
        "improves", "outperform", "profit", "profits", "record", "rise", "rises",
        "strong", "surge", "surges", "upgrade", "upside",
    }
)
_NEGATIVE = frozenset(
    {
        "bearish", "cut", "cuts", "decline", "declines", "downgrade", "drop", "drops",
        "fall", "falls", "fraud", "investigation", "lawsuit", "loss", "losses", "miss",
        "misses", "risk", "risks", "slump", "weak", "warning",
    }
)


def latest_news_features(articles: list[dict]) -> dict[str, float]:
    """`latest_news_features`은(는) 필요한 데이터를 조회해 반환합니다."""

    return _features_for_date(articles, datetime.now(timezone.utc).date() + timedelta(days=1))


def build_news_training_rows(
    articles: list[dict],
    candles: list[Candle],
    *,
    horizon_days: int = 3,
    minimum_articles: int = 0,
    minimum_absolute_excess_return: float = 0.0,
    benchmark_candles: list[Candle] | None = None,
) -> list[dict]:
    """`build_news_training_rows`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

    if horizon_days < 1:
        raise ValueError("horizon_days must be positive")
    if minimum_articles < 0 or not 0 <= minimum_absolute_excess_return <= 1:
        raise ValueError("news quality thresholds are invalid")
    published_dates = [_published_date(article) for article in articles]
    valid_dates = [value for value in published_dates if value is not None]
    if not valid_dates:
        return []
    earliest = min(valid_dates) + timedelta(days=1)
    latest = max(valid_dates) + timedelta(days=2)
    ordered = sorted(candles, key=lambda candle: candle.timestamp)
    benchmark_closes = {
        candle.timestamp.date(): float(candle.close) for candle in benchmark_candles or []
    }
    candidates = []
    for candle in ordered:
        trade_date = candle.timestamp.date()
        if not earliest <= trade_date <= latest:
            continue
        candidates.append(
            {
                "timestamp": trade_date.isoformat(),
                "_close": float(candle.close),
                **_features_for_date(articles, trade_date),
            }
        )
    rows = []
    for index in range(len(candidates) - horizon_days):
        current = candidates[index]
        if float(current["article_count_3d"]) < math.log1p(minimum_articles):
            continue
        future = candidates[index + horizon_days]
        future_return = float(future["_close"]) / float(current["_close"]) - 1
        benchmark_return = _benchmark_return(
            benchmark_closes,
            date.fromisoformat(str(current["timestamp"])),
            date.fromisoformat(str(future["timestamp"])),
        )
        if benchmark_candles and benchmark_return is None:
            continue
        excess_return = (
            future_return - benchmark_return
            if benchmark_return is not None
            else future_return
        )
        if abs(excess_return) < minimum_absolute_excess_return:
            continue
        features = {name: current[name] for name in NEWS_FEATURES}
        rows.append(
            {
                "timestamp": current["timestamp"],
                **features,
                "future_return": future_return,
                "benchmark_future_return": benchmark_return,
                "future_excess_return": excess_return,
                "label": int(excess_return > 0),
            }
        )
    return rows


def _benchmark_return(
    closes: dict[date, float], start: date, end: date
) -> float | None:
    """`_benchmark_return`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    current = closes.get(start)
    future = closes.get(end)
    if not current or not future:
        return None
    return future / current - 1


def _features_for_date(articles: list[dict], reference_date: date) -> dict[str, float]:
    """`_features_for_date`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    start = reference_date - timedelta(days=3)
    selected = [
        article
        for article in articles
        if (published := _published_date(article)) is not None
        and start <= published < reference_date
    ]
    positive = 0
    negative = 0
    title_lengths = []
    sources = set()
    for article in selected:
        title = str(article.get("title") or "")
        text = f"{title} {article.get('description') or ''}".casefold()
        words = set(re.findall(r"[a-z]+", text))
        positive += len(words & _POSITIVE)
        negative += len(words & _NEGATIVE)
        title_lengths.append(len(title))
        source = (article.get("source") or {}).get("name")
        if source:
            sources.add(str(source).casefold())
    sentiment_total = positive + negative
    article_count = len(selected)
    return {
        "article_count_3d": math.log1p(article_count),
        "positive_ratio": positive / max(sentiment_total, 1),
        "negative_ratio": negative / max(sentiment_total, 1),
        "sentiment_balance": (positive - negative) / max(sentiment_total, 1),
        "source_diversity": len(sources) / max(article_count, 1),
        "average_title_length": sum(title_lengths) / max(article_count, 1) / 100,
    }


def _published_date(article: dict) -> date | None:
    """`_published_date`은(는) 연결 또는 메시지 전달 생명주기를 관리합니다."""

    raw = article.get("publishedAt")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).date()
    except ValueError:
        return None
