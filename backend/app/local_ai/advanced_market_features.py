"""과거 종가와 동시점 종목군만 사용하는 기술 AI 후보 피처를 계산한다."""

from collections import defaultdict
from math import isfinite

import numpy as np


ADVANCED_TECHNICAL_FEATURES = (
    "return_20d",
    "return_60d",
    "volatility_60",
    "volatility_percentile_252",
    "return_skew_20",
    "return_kurtosis_20",
    "return_autocorrelation_20",
    "up_day_ratio_20",
    "trend_efficiency_20",
    "current_drawdown_60",
    "downside_upside_volatility_ratio_60",
    "return_5d_cross_section_rank",
    "return_20d_cross_section_rank",
    "volatility_20_cross_section_rank",
    "cross_section_return_dispersion_5d",
    "cross_section_positive_breadth_5d",
)

MINIMUM_ADVANCED_HISTORY = 253


def enrich_advanced_technical_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    """기술 데이터 행에 누수 없는 시계열·횡단면 후보 피처를 덧붙인다."""
    by_symbol: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_symbol[row["symbol"]].append(row)

    enriched: list[dict[str, object]] = []
    for symbol_rows in by_symbol.values():
        symbol_rows.sort(key=lambda item: item["timestamp"])
        closes = np.asarray([float(row["close_price"]) for row in symbol_rows], dtype=float)
        if len(closes) < MINIMUM_ADVANCED_HISTORY:
            continue
        returns = closes[1:] / closes[:-1] - 1.0
        rolling_volatility = _rolling_volatility(returns, window=20)
        for index in range(MINIMUM_ADVANCED_HISTORY - 1, len(symbol_rows)):
            feature_values = _time_series_features(
                closes,
                returns,
                rolling_volatility,
                index,
            )
            if all(isfinite(value) for value in feature_values.values()):
                enriched.append({**symbol_rows[index], **feature_values})

    enriched.sort(key=lambda item: (str(item["timestamp"]), str(item["symbol"])))
    _add_cross_section_features(enriched)
    return [
        row
        for row in enriched
        if all(isfinite(float(row[name])) for name in ADVANCED_TECHNICAL_FEATURES)
    ]


def _time_series_features(
    closes: np.ndarray,
    returns: np.ndarray,
    rolling_volatility: np.ndarray,
    index: int,
) -> dict[str, float]:
    """한 종목의 현재 인덱스 이전 값만으로 후보 피처를 계산한다."""
    recent_returns = returns[index - 20 : index]
    medium_returns = returns[index - 60 : index]
    recent_closes = closes[index - 20 : index + 1]
    medium_closes = closes[index - 59 : index + 1]
    volatility_history = rolling_volatility[max(19, index - 251) : index + 1]
    current_volatility = rolling_volatility[index]

    centered = recent_returns - recent_returns.mean()
    standard_deviation = recent_returns.std(ddof=0)
    standardized = centered / standard_deviation if standard_deviation > 1e-12 else centered
    positive = np.maximum(medium_returns, 0.0)
    negative = np.minimum(medium_returns, 0.0)
    upside = float(np.sqrt(np.mean(positive**2)))
    downside = float(np.sqrt(np.mean(negative**2)))
    path_length = float(np.abs(np.diff(recent_closes)).sum())

    return {
        "return_20d": float(closes[index] / closes[index - 20] - 1.0),
        "return_60d": float(closes[index] / closes[index - 60] - 1.0),
        "volatility_60": float(medium_returns.std(ddof=0)),
        "volatility_percentile_252": float(
            np.mean(volatility_history <= current_volatility)
        ),
        "return_skew_20": float(np.mean(standardized**3)),
        "return_kurtosis_20": float(np.mean(standardized**4) - 3.0),
        "return_autocorrelation_20": _correlation(
            recent_returns[:-1], recent_returns[1:]
        ),
        "up_day_ratio_20": float(np.mean(recent_returns > 0.0)),
        "trend_efficiency_20": float(
            abs(recent_closes[-1] - recent_closes[0]) / max(path_length, 1e-12)
        ),
        "current_drawdown_60": float(closes[index] / medium_closes.max() - 1.0),
        "downside_upside_volatility_ratio_60": downside / max(upside, 1e-12),
    }


def _rolling_volatility(returns: np.ndarray, *, window: int) -> np.ndarray:
    """각 종가 인덱스에서 확인 가능한 최근 수익률 변동성을 만든다."""
    values = np.full(len(returns) + 1, np.nan, dtype=float)
    for index in range(window, len(values)):
        values[index] = returns[index - window : index].std(ddof=0)
    return values


def _add_cross_section_features(rows: list[dict[str, object]]) -> None:
    """같은 시점에 존재하는 종목끼리만 상대순위와 시장 폭을 계산한다."""
    by_timestamp: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_timestamp[str(row["timestamp"])].append(row)
    for timestamp_rows in by_timestamp.values():
        return_5d = np.asarray([float(row["return_5d"]) for row in timestamp_rows])
        return_20d = np.asarray([float(row["return_20d"]) for row in timestamp_rows])
        volatility_20 = np.asarray(
            [float(row["volatility_20"]) for row in timestamp_rows]
        )
        ranks = (
            _percentile_ranks(return_5d),
            _percentile_ranks(return_20d),
            _percentile_ranks(volatility_20),
        )
        dispersion = float(return_5d.std(ddof=0))
        breadth = float(np.mean(return_5d > 0.0))
        for index, row in enumerate(timestamp_rows):
            row.update(
                return_5d_cross_section_rank=float(ranks[0][index]),
                return_20d_cross_section_rank=float(ranks[1][index]),
                volatility_20_cross_section_rank=float(ranks[2][index]),
                cross_section_return_dispersion_5d=dispersion,
                cross_section_positive_breadth_5d=breadth,
            )


def _percentile_ranks(values: np.ndarray) -> np.ndarray:
    """동률에 평균 순위를 부여하는 0~1 범위의 횡단면 순위를 반환한다."""
    order = np.argsort(values, kind="stable")
    ranks = np.empty(len(values), dtype=float)
    sorted_values = values[order]
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and sorted_values[end] == sorted_values[start]:
            end += 1
        average_rank = ((start + 1) + end) / 2.0 / len(values)
        ranks[order[start:end]] = average_rank
        start = end
    return ranks


def _correlation(left: np.ndarray, right: np.ndarray) -> float:
    """상수 구간에서는 중립값 0을 반환해 비유한 숫자를 방지한다."""
    if left.std(ddof=0) <= 1e-12 or right.std(ddof=0) <= 1e-12:
        return 0.0
    return float(np.corrcoef(left, right)[0, 1])
