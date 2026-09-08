"""context_features 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from __future__ import annotations


FINANCIAL_TREND_FEATURES = (
    "revenue_growth_acceleration",
    "net_income_growth_acceleration",
    "margin_change",
    "leverage_change",
)

NEWS_TREND_FEATURES = (
    "sentiment_change",
    "article_count_change",
    "sentiment_mean_3",
    "source_diversity_change",
)


def add_financial_trends(rows: list[dict]) -> list[dict]:
    """`add_financial_trends`은(는) 데이터를 저장하거나 기존 상태에 추가합니다."""

    return _add_grouped_trends(rows, _financial_changes)


def add_news_trends(rows: list[dict]) -> list[dict]:
    """`add_news_trends`은(는) 데이터를 저장하거나 기존 상태에 추가합니다."""

    grouped = _group_rows(rows)
    enriched = []
    for symbol_rows in grouped.values():
        for index in range(1, len(symbol_rows)):
            current = symbol_rows[index]
            previous = symbol_rows[index - 1]
            balances = [
                float(row["sentiment_balance"])
                for row in symbol_rows[max(0, index - 2) : index + 1]
            ]
            enriched.append(
                {
                    **current,
                    "sentiment_change": float(current["sentiment_balance"])
                    - float(previous["sentiment_balance"]),
                    "article_count_change": float(current["article_count_3d"])
                    - float(previous["article_count_3d"]),
                    "sentiment_mean_3": sum(balances) / len(balances),
                    "source_diversity_change": float(current["source_diversity"])
                    - float(previous["source_diversity"]),
                }
            )
    return sorted(enriched, key=lambda row: (row["timestamp"], row["symbol"]))


def _add_grouped_trends(rows: list[dict], change_builder) -> list[dict]:
    """`_add_grouped_trends`은(는) 데이터를 저장하거나 기존 상태에 추가합니다."""

    enriched = []
    for symbol_rows in _group_rows(rows).values():
        for index in range(1, len(symbol_rows)):
            enriched.append(
                {
                    **symbol_rows[index],
                    **change_builder(symbol_rows[index], symbol_rows[index - 1]),
                }
            )
    return sorted(enriched, key=lambda row: (row["timestamp"], row["symbol"]))


def _financial_changes(current: dict, previous: dict) -> dict[str, float]:
    """`_financial_changes`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return {
        "revenue_growth_acceleration": float(current["revenue_growth_yoy"])
        - float(previous["revenue_growth_yoy"]),
        "net_income_growth_acceleration": float(current["net_income_growth_yoy"])
        - float(previous["net_income_growth_yoy"]),
        "margin_change": float(current["net_margin"]) - float(previous["net_margin"]),
        "leverage_change": float(current["debt_to_assets"])
        - float(previous["debt_to_assets"]),
    }


def _group_rows(rows: list[dict]) -> dict[str, list[dict]]:
    """`_group_rows`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(str(row["symbol"]), []).append(row)
    for symbol_rows in grouped.values():
        symbol_rows.sort(key=lambda row: str(row["timestamp"]))
    return grouped
