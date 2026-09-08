"""KIS 국내 투자자 수급을 시점 안전한 학습 피처로 변환한다."""

from __future__ import annotations

from datetime import date

import numpy as np

from app.investor_flow.kis import DailyKisInvestorFlow
from app.local_ai.market_features import build_market_training_rows
from app.providers.contracts import Candle


KIS_FLOW_FEATURES = (
    "foreign_net_volume_ratio",
    "institution_net_volume_ratio",
    "individual_net_volume_ratio",
    "foreign_ratio_5d",
    "institution_ratio_5d",
    "foreign_ratio_20d",
    "institution_ratio_20d",
    "foreign_flow_zscore_20d",
    "institution_flow_zscore_20d",
    "foreign_institution_agreement_5d",
    "price_return_1d",
    "price_return_5d",
    "price_sma_20_gap",
    "price_volatility_20",
    "price_volume_ratio",
    "market_return_5d",
    "market_sma_20_gap",
    "relative_return_5d",
    "relative_sma_20_gap",
)


def build_kis_flow_training_rows(
    flows: list[DailyKisInvestorFlow],
    candles: list[Candle],
    *,
    benchmark_candles: list[Candle],
    horizon_days: int = 5,
    minimum_absolute_excess_return: float = 0.005,
) -> list[dict]:
    """공개된 당일 수급만 사용해 이후 벤치마크 대비 하락 여부를 만든다."""

    if horizon_days < 1:
        raise ValueError("horizon_days must be positive")
    prices = {item.timestamp.date(): float(item.close) for item in candles}
    volumes = {item.timestamp.date(): max(float(item.volume), 1.0) for item in candles}
    benchmark = {item.timestamp.date(): float(item.close) for item in benchmark_candles}
    market_by_date = {
        date.fromisoformat(row.timestamp[:10]): {
            "price_return_1d": row.technical["return_1d"],
            "price_return_5d": row.technical["return_5d"],
            "price_sma_20_gap": row.technical["sma_20_gap"],
            "price_volatility_20": row.technical["volatility_20"],
            "price_volume_ratio": row.technical["volume_ratio"],
            "market_return_5d": row.technical["market_return_5d"],
            "market_sma_20_gap": row.technical["market_sma_20_gap"],
            "relative_return_5d": row.technical["relative_return_5d"],
            "relative_sma_20_gap": row.technical["relative_sma_20_gap"],
        }
        for row in build_market_training_rows(
            candles,
            horizon_days=1,
            benchmark_candles=benchmark_candles,
        )
    }
    dates = sorted(prices)
    indexes = {value: index for index, value in enumerate(dates)}
    daily = [item for item in sorted(flows, key=lambda value: value.trade_date) if item.trade_date in prices]
    ratios = [
        (
            item.trade_date,
            float(item.foreign_net_quantity) / volumes[item.trade_date],
            float(item.institution_net_quantity) / volumes[item.trade_date],
            float(item.individual_net_quantity) / volumes[item.trade_date],
        )
        for item in daily
    ]
    rows: list[dict] = []
    for index in range(19, len(ratios)):
        current_date = ratios[index][0]
        price_index = indexes[current_date]
        if price_index + horizon_days >= len(dates):
            continue
        future_date = dates[price_index + horizon_days]
        if current_date not in benchmark or future_date not in benchmark:
            continue
        market_features = market_by_date.get(current_date)
        if market_features is None:
            continue
        future_return = prices[future_date] / prices[current_date] - 1
        benchmark_return = benchmark[future_date] / benchmark[current_date] - 1
        excess_return = future_return - benchmark_return
        if abs(excess_return) < minimum_absolute_excess_return:
            continue
        rows.append(
            {
                "timestamp": current_date.isoformat(),
                **_features_at(ratios, index),
                **market_features,
                "future_return": future_return,
                "benchmark_future_return": benchmark_return,
                "future_excess_return": excess_return,
                "label": int(excess_return < 0),
            }
        )
    return rows


def _features_at(ratios: list[tuple[date, float, float, float]], index: int) -> dict[str, float]:
    """`_features_at`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    window = np.asarray([item[1:] for item in ratios[index - 19 : index + 1]], dtype=float)
    foreign, institution, individual = window.T
    return {
        "foreign_net_volume_ratio": float(foreign[-1]),
        "institution_net_volume_ratio": float(institution[-1]),
        "individual_net_volume_ratio": float(individual[-1]),
        "foreign_ratio_5d": float(foreign[-5:].mean()),
        "institution_ratio_5d": float(institution[-5:].mean()),
        "foreign_ratio_20d": float(foreign.mean()),
        "institution_ratio_20d": float(institution.mean()),
        "foreign_flow_zscore_20d": _zscore(foreign),
        "institution_flow_zscore_20d": _zscore(institution),
        "foreign_institution_agreement_5d": float(
            np.mean(np.sign(foreign[-5:]) == np.sign(institution[-5:]))
        ),
    }


def _zscore(values: np.ndarray) -> float:
    """`_zscore`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    deviation = float(values.std())
    return float((values[-1] - values.mean()) / deviation) if deviation > 1e-12 else 0.0
