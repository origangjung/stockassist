"""market_features 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.providers.contracts import Candle


TECHNICAL_FEATURES = (
    "return_1d",
    "return_5d",
    "sma_5_gap",
    "sma_20_gap",
    "volatility_20",
    "volume_ratio",
    "rsi_14",
)
BENCHMARK_TECHNICAL_FEATURES = (
    "market_return_5d",
    "market_sma_20_gap",
    "relative_return_5d",
    "relative_sma_20_gap",
)
RISK_FEATURES = (
    "volatility_20",
    "drawdown_20",
    "downside_deviation_20",
    "range_width_20",
    "volume_ratio",
    "market_volatility_20",
    "relative_volatility_20",
)
LONG_HORIZON_RISK_FEATURES = (
    "return_20d",
    "sma_60_gap",
    "volatility_60",
    "drawdown_60",
    "downside_deviation_60",
    "volatility_ratio_20_60",
)


@dataclass(frozen=True)
class MarketTrainingRow:
    """`MarketTrainingRow` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    timestamp: str
    close_price: float
    technical: dict[str, float]
    risk: dict[str, float]
    technical_label: int
    risk_label: int
    future_return: float
    benchmark_future_return: float | None
    future_excess_return: float | None
    future_max_drawdown: float


def latest_market_features(
    candles: list[Candle], benchmark_candles: list[Candle] | None = None
) -> dict[str, float] | None:
    """`latest_market_features`은(는) 필요한 데이터를 조회해 반환합니다."""

    ordered = sorted(candles, key=lambda candle: candle.timestamp)
    if len(ordered) < 21:
        return None
    technical, risk = _features_at(ordered, len(ordered) - 1)
    if benchmark_candles:
        benchmark = sorted(benchmark_candles, key=lambda candle: candle.timestamp)
        if len(benchmark) >= 21:
            benchmark_technical, benchmark_risk = _features_at(benchmark, len(benchmark) - 1)
            _add_benchmark_features(technical, risk, benchmark_technical, benchmark_risk)
    return {**technical, **{f"risk_{name}": value for name, value in risk.items()}}


def build_market_training_rows(
    candles: list[Candle], *, horizon_days: int = 5, risk_threshold: float = -0.03,
    benchmark_candles: list[Candle] | None = None,
    include_long_horizon_risk: bool = False,
) -> list[MarketTrainingRow]:
    """`build_market_training_rows`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

    if horizon_days < 1:
        raise ValueError("horizon_days must be positive")
    ordered = sorted(candles, key=lambda candle: candle.timestamp)
    benchmark_features = _features_by_date(benchmark_candles or [])
    benchmark_closes = {
        candle.timestamp.date(): float(candle.close) for candle in benchmark_candles or []
    }
    rows: list[MarketTrainingRow] = []
    start_index = 60 if include_long_horizon_risk else 20
    for index in range(start_index, len(ordered) - horizon_days):
        technical, risk = _features_at(ordered, index)
        if include_long_horizon_risk:
            risk.update(_long_horizon_risk_features(ordered, index, risk))
        benchmark = benchmark_features.get(ordered[index].timestamp.date())
        if benchmark is not None:
            _add_benchmark_features(technical, risk, *benchmark)
        current = float(ordered[index].close)
        future = ordered[index + 1 : index + horizon_days + 1]
        future_close = float(future[-1].close)
        future_return = future_close / current - 1
        worst_return = min(float(candle.low) / current - 1 for candle in future)
        running_peak = current
        future_max_drawdown = 0.0
        for candle in future:
            running_peak = max(running_peak, float(candle.high))
            future_max_drawdown = min(
                future_max_drawdown,
                float(candle.low) / running_peak - 1,
            )
        current_benchmark = benchmark_closes.get(ordered[index].timestamp.date())
        future_benchmark = benchmark_closes.get(future[-1].timestamp.date())
        benchmark_future_return = (
            future_benchmark / current_benchmark - 1
            if current_benchmark and future_benchmark
            else None
        )
        future_excess_return = (
            future_return - benchmark_future_return
            if benchmark_future_return is not None
            else None
        )
        rows.append(
            MarketTrainingRow(
                timestamp=ordered[index].timestamp.isoformat(),
                close_price=current,
                technical=technical,
                risk=risk,
                technical_label=int(
                    (future_excess_return if future_excess_return is not None else future_return)
                    > 0
                ),
                risk_label=int(worst_return <= risk_threshold),
                future_return=future_return,
                benchmark_future_return=benchmark_future_return,
                future_excess_return=future_excess_return,
                future_max_drawdown=future_max_drawdown,
            )
        )
    return rows


def _features_by_date(
    candles: list[Candle],
) -> dict[object, tuple[dict[str, float], dict[str, float]]]:
    """`_features_by_date`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    ordered = sorted(candles, key=lambda candle: candle.timestamp)
    return {
        ordered[index].timestamp.date(): _features_at(ordered, index)
        for index in range(20, len(ordered))
    }


def _add_benchmark_features(
    technical: dict[str, float],
    risk: dict[str, float],
    benchmark_technical: dict[str, float],
    benchmark_risk: dict[str, float],
) -> None:
    """`_add_benchmark_features`은(는) 데이터를 저장하거나 기존 상태에 추가합니다."""

    technical.update(
        {
            "market_return_5d": benchmark_technical["return_5d"],
            "market_sma_20_gap": benchmark_technical["sma_20_gap"],
            "relative_return_5d": technical["return_5d"]
            - benchmark_technical["return_5d"],
            "relative_sma_20_gap": technical["sma_20_gap"]
            - benchmark_technical["sma_20_gap"],
        }
    )
    risk.update(
        {
            "market_volatility_20": benchmark_risk["volatility_20"],
            "relative_volatility_20": risk["volatility_20"]
            - benchmark_risk["volatility_20"],
        }
    )


def _features_at(candles: list[Candle], index: int) -> tuple[dict[str, float], dict[str, float]]:
    """`_features_at`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    window = candles[index - 20 : index + 1]
    close = np.asarray([float(candle.close) for candle in window], dtype=float)
    high = np.asarray([float(candle.high) for candle in window], dtype=float)
    low = np.asarray([float(candle.low) for candle in window], dtype=float)
    volume = np.asarray([float(candle.volume) for candle in window], dtype=float)
    returns = np.diff(close) / close[:-1]
    negative_returns = np.minimum(returns, 0.0)
    gains = np.maximum(np.diff(close[-15:]), 0.0).mean()
    losses = -np.minimum(np.diff(close[-15:]), 0.0).mean()
    rsi = 1.0 if losses == 0 else 1 - (1 / (1 + gains / losses))
    volume_ratio = volume[-1] / max(volume[:-1].mean(), 1.0)
    range_width = (high[-20:].max() - low[-20:].min()) / max(close[-1], 1e-9)
    technical = {
        "return_1d": close[-1] / close[-2] - 1,
        "return_5d": close[-1] / close[-6] - 1,
        "sma_5_gap": close[-1] / close[-5:].mean() - 1,
        "sma_20_gap": close[-1] / close[-20:].mean() - 1,
        "volatility_20": float(returns[-20:].std(ddof=0)),
        "volume_ratio": float(volume_ratio),
        "rsi_14": float(rsi),
    }
    running_peak = np.maximum.accumulate(close)
    risk = {
        "volatility_20": technical["volatility_20"],
        "drawdown_20": float((close / running_peak - 1).min()),
        "downside_deviation_20": float(np.sqrt(np.mean(negative_returns**2))),
        "range_width_20": float(range_width),
        "volume_ratio": float(volume_ratio),
    }
    return technical, risk


def _long_horizon_risk_features(
    candles: list[Candle], index: int, risk: dict[str, float]
) -> dict[str, float]:
    """`_long_horizon_risk_features`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    window = candles[index - 60 : index + 1]
    close = np.asarray([float(candle.close) for candle in window], dtype=float)
    returns = np.diff(close) / close[:-1]
    negative_returns = np.minimum(returns, 0.0)
    running_peak = np.maximum.accumulate(close)
    volatility_60 = float(returns.std(ddof=0))
    return {
        "return_20d": float(close[-1] / close[-21] - 1),
        "sma_60_gap": float(close[-1] / close[-60:].mean() - 1),
        "volatility_60": volatility_60,
        "drawdown_60": float((close / running_peak - 1).min()),
        "downside_deviation_60": float(np.sqrt(np.mean(negative_returns**2))),
        "volatility_ratio_20_60": float(
            risk["volatility_20"] / max(volatility_60, 1e-9)
        ),
    }
