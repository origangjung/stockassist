"""Qlib식 횡단면 비교 특성을 과거·현재 시점 데이터만으로 계산한다."""

from __future__ import annotations

from collections import defaultdict
from math import isfinite

import numpy as np


TARGET_RANK_COLUMN = "future_excess_return_cross_section_rank"


def enrich_cross_section_rows(
    rows: list[dict[str, str]], feature_names: tuple[str, ...]
) -> tuple[list[dict[str, object]], tuple[str, ...]]:
    """같은 시각의 종목 집합에서 각 특성의 순위와 표준점수를 추가한다."""

    output_names = tuple(
        name
        for feature in feature_names
        for name in (
            f"{feature}_cross_section_rank",
            f"{feature}_cross_section_zscore",
        )
    )
    by_timestamp: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_timestamp[str(row["timestamp"])].append(row)

    enriched: list[dict[str, object]] = []
    for timestamp_rows in by_timestamp.values():
        if len(timestamp_rows) < 5:
            continue
        additions = [dict() for _row in timestamp_rows]
        for feature in feature_names:
            values = np.asarray([float(row[feature]) for row in timestamp_rows], dtype=float)
            if not np.all(np.isfinite(values)):
                raise ValueError(f"{feature} contains a non-finite value")
            ranks = _percentile_ranks(values)
            standard_deviation = float(values.std(ddof=0))
            zscores = (
                (values - float(values.mean())) / standard_deviation
                if standard_deviation > 1e-12
                else np.zeros(len(values), dtype=float)
            )
            for index in range(len(timestamp_rows)):
                additions[index][f"{feature}_cross_section_rank"] = float(ranks[index])
                additions[index][f"{feature}_cross_section_zscore"] = float(zscores[index])
        enriched.extend(
            {**row, **addition}
            for row, addition in zip(timestamp_rows, additions, strict=True)
        )

    enriched.sort(key=lambda row: (str(row["timestamp"]), str(row.get("symbol", ""))))
    return (
        [
            row
            for row in enriched
            if all(isfinite(float(row[name])) for name in output_names)
        ],
        output_names,
    )


def relabel_cross_section_outcomes(
    rows: list[dict[str, str]],
    *,
    outcome_column: str = "future_excess_return",
    tail_fraction: float = 0.25,
    minimum_symbols: int = 5,
) -> list[dict[str, object]]:
    """동일 시점의 미래 초과수익 상·하위 꼬리만 남겨 방향 라벨을 만든다.

    각 시점 안에서만 순위를 계산하므로 종목별 가격 규모와 시장 국면의 영향을
    줄인다. 중간 순위는 학습에서 제외해 작은 무작위 움직임을 정답으로 강요하지
    않으며, 원시 미래수익은 오직 평가용 열로 보존한다.
    """

    if not 0.0 < tail_fraction < 0.5:
        raise ValueError("tail fraction must be between zero and one half")
    if minimum_symbols < 3:
        raise ValueError("minimum symbols must be at least three")

    by_timestamp: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_timestamp[str(row["timestamp"])].append(row)

    relabeled: list[dict[str, object]] = []
    for timestamp_rows in by_timestamp.values():
        if len(timestamp_rows) < minimum_symbols:
            continue
        try:
            outcomes = np.asarray(
                [float(row[outcome_column]) for row in timestamp_rows], dtype=float
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{outcome_column} must contain numeric values") from exc
        if not np.all(np.isfinite(outcomes)):
            raise ValueError(f"{outcome_column} contains a non-finite value")

        ranks = _zero_to_one_percentile_ranks(outcomes)
        for row, rank in zip(timestamp_rows, ranks, strict=True):
            if rank <= tail_fraction:
                label = 0
            elif rank >= 1.0 - tail_fraction:
                label = 1
            else:
                continue
            relabeled.append(
                {
                    **row,
                    TARGET_RANK_COLUMN: float(rank),
                    "label": label,
                    "label_basis": "cross_section_future_excess_return_tail",
                }
            )

    relabeled.sort(
        key=lambda row: (str(row["timestamp"]), str(row.get("symbol", "")))
    )
    return relabeled


def _percentile_ranks(values: np.ndarray) -> np.ndarray:
    """동점은 평균 순위를 부여해 0 초과 1 이하의 분위 순위를 반환한다."""

    order = np.argsort(values, kind="stable")
    sorted_values = values[order]
    ranks = np.empty(len(values), dtype=float)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and sorted_values[end] == sorted_values[start]:
            end += 1
        ranks[order[start:end]] = ((start + 1) + end) / 2.0 / len(values)
        start = end
    return ranks


def _zero_to_one_percentile_ranks(values: np.ndarray) -> np.ndarray:
    """동률은 평균 순위를 사용해 최솟값 0, 최댓값 1인 순위를 반환한다."""

    if len(values) < 2:
        return np.zeros(len(values), dtype=float)
    return (_percentile_ranks(values) * len(values) - 1.0) / (len(values) - 1.0)
