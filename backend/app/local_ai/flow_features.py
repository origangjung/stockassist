"""flow_features 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import math

import numpy as np

from app.providers.contracts import Candle


FLOW_FEATURES = (
    "short_volume_ratio",
    "short_exempt_ratio",
    "short_ratio_5d",
    "short_ratio_20d",
    "short_ratio_change_5d",
    "reported_volume_ratio_20d",
)

SHORT_INTEREST_FEATURES = (
    "short_interest_change",
    "days_to_cover_log",
    "short_interest_change_acceleration",
)


@dataclass(frozen=True)
class DailyShortVolume:
    """`DailyShortVolume` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    trade_date: date
    short_quantity: float
    short_exempt_quantity: float
    total_quantity: float


def aggregate_short_volume(records: list[dict]) -> list[DailyShortVolume]:
    """`aggregate_short_volume`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    totals: dict[date, list[float]] = {}
    for record in records:
        raw_date = record.get("tradeReportDate")
        if not raw_date:
            continue
        trade_date = date.fromisoformat(str(raw_date)[:10])
        values = totals.setdefault(trade_date, [0.0, 0.0, 0.0])
        values[0] += _nonnegative(record.get("shortParQuantity"))
        values[1] += _nonnegative(record.get("shortExemptParQuantity"))
        values[2] += _nonnegative(record.get("totalParQuantity"))
    return [
        DailyShortVolume(trade_date, values[0], values[1], values[2])
        for trade_date, values in sorted(totals.items())
        if values[2] > 0
    ]


def latest_flow_features(records: list[dict]) -> dict[str, float] | None:
    """`latest_flow_features`은(는) 필요한 데이터를 조회해 반환합니다."""

    daily = aggregate_short_volume(records)
    return _features_at(daily, len(daily) - 1) if len(daily) >= 20 else None


def short_interest_features_by_date(
    records: list[dict], target_dates: list[date]
) -> dict[date, dict[str, float]]:
    """`short_interest_features_by_date`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    releases = []
    for record in records:
        try:
            settlement = date.fromisoformat(str(record["settlementDate"])[:10])
            current = max(float(record["currentShortPositionQuantity"]), 0.0)
            previous = max(float(record["previousShortPositionQuantity"]), 0.0)
            days_to_cover = max(float(record.get("daysToCoverQuantity") or 0.0), 0.0)
        except (KeyError, TypeError, ValueError):
            continue
        change = (current - previous) / max(previous, 1.0)
        releases.append((settlement + timedelta(days=14), change, days_to_cover))
    releases.sort(key=lambda item: item[0])
    result = {}
    release_index = -1
    for target in sorted(set(target_dates)):
        while release_index + 1 < len(releases) and releases[release_index + 1][0] <= target:
            release_index += 1
        if release_index < 0:
            continue
        _, change, days_to_cover = releases[release_index]
        previous_change = releases[release_index - 1][1] if release_index > 0 else 0.0
        result[target] = {
            "short_interest_change": change,
            "days_to_cover_log": math.log1p(days_to_cover),
            "short_interest_change_acceleration": change - previous_change,
        }
    return result


def build_flow_training_rows(
    records: list[dict],
    candles: list[Candle],
    *,
    horizon_days: int = 5,
    minimum_absolute_excess_return: float = 0.0,
    benchmark_candles: list[Candle] | None = None,
) -> list[dict]:
    """`build_flow_training_rows`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

    if horizon_days < 1:
        raise ValueError("horizon_days must be positive")
    if not 0 <= minimum_absolute_excess_return <= 1:
        raise ValueError("minimum absolute excess return is invalid")
    daily = aggregate_short_volume(records)
    prices = {candle.timestamp.date(): float(candle.close) for candle in candles}
    price_dates = sorted(prices)
    price_index = {trade_date: index for index, trade_date in enumerate(price_dates)}
    benchmark_prices = {
        candle.timestamp.date(): float(candle.close) for candle in benchmark_candles or []
    }
    rows: list[dict] = []
    for index in range(19, len(daily)):
        current_date = daily[index].trade_date
        candle_index = price_index.get(current_date)
        if candle_index is None or candle_index + horizon_days >= len(price_dates):
            continue
        future_date = price_dates[candle_index + horizon_days]
        future_return = prices[future_date] / prices[current_date] - 1
        current_benchmark = benchmark_prices.get(current_date)
        future_benchmark = benchmark_prices.get(future_date)
        benchmark_return = (
            future_benchmark / current_benchmark - 1
            if current_benchmark and future_benchmark
            else None
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
        rows.append(
            {
                "timestamp": current_date.isoformat(),
                **_features_at(daily, index),
                "future_return": future_return,
                "benchmark_future_return": benchmark_return,
                "future_excess_return": excess_return,
                "label": int(excess_return < 0),
            }
        )
    return rows


def _features_at(daily: list[DailyShortVolume], index: int) -> dict[str, float]:
    """`_features_at`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    window = daily[index - 19 : index + 1]
    short_ratios = np.asarray(
        [item.short_quantity / item.total_quantity for item in window], dtype=float
    )
    exempt_ratios = np.asarray(
        [item.short_exempt_quantity / item.total_quantity for item in window], dtype=float
    )
    volumes = np.asarray([item.total_quantity for item in window], dtype=float)
    return {
        "short_volume_ratio": float(short_ratios[-1]),
        "short_exempt_ratio": float(exempt_ratios[-1]),
        "short_ratio_5d": float(short_ratios[-5:].mean()),
        "short_ratio_20d": float(short_ratios.mean()),
        "short_ratio_change_5d": float(short_ratios[-1] - short_ratios[-5:].mean()),
        "reported_volume_ratio_20d": float(volumes[-1] / max(volumes[:-1].mean(), 1.0)),
    }


def _nonnegative(value) -> float:
    """`_nonnegative`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    try:
        return max(float(value or 0), 0.0)
    except (TypeError, ValueError):
        return 0.0
