from dataclasses import dataclass
from datetime import datetime

import numpy as np

from app.providers.contracts import Candle


@dataclass(frozen=True)
class FeatureDataset:
    features: np.ndarray
    labels: np.ndarray
    prediction_features: np.ndarray
    feature_names: tuple[str, ...]
    data_as_of: datetime


FEATURE_NAMES = (
    "return_1d",
    "return_5d",
    "sma_5_gap",
    "sma_20_gap",
    "volatility_20",
    "volume_ratio",
    "rsi_14",
)


def build_feature_dataset(
    candles: list[Candle], horizon_days: int, lookback: int = 20
) -> FeatureDataset:
    if horizon_days < 1:
        raise ValueError("horizon_days must be positive")
    if len(candles) < lookback + horizon_days + 20:
        raise ValueError("at least 45 candles are required for prediction")
    ordered = sorted(candles, key=lambda candle: candle.timestamp)
    close = np.array([float(candle.close) for candle in ordered], dtype=float)
    volume = np.array([float(candle.volume) for candle in ordered], dtype=float)
    rows: list[np.ndarray] = []
    labels: list[int] = []
    for index in range(lookback, len(ordered) - horizon_days):
        rows.append(_features_at(close, volume, index))
        labels.append(int(close[index + horizon_days] > close[index]))
    return FeatureDataset(
        features=np.vstack(rows),
        labels=np.asarray(labels, dtype=np.int8),
        prediction_features=_features_at(close, volume, len(ordered) - 1).reshape(1, -1),
        feature_names=FEATURE_NAMES,
        data_as_of=ordered[-1].timestamp,
    )


def _features_at(close: np.ndarray, volume: np.ndarray, index: int) -> np.ndarray:
    history = close[: index + 1]
    volumes = volume[: index + 1]
    returns = np.diff(history) / history[:-1]
    sma_5 = history[-5:].mean()
    sma_20 = history[-20:].mean()
    gains = np.clip(np.diff(history[-15:]), 0, None).mean()
    losses = -np.clip(np.diff(history[-15:]), None, 0).mean()
    rsi = 100.0 if losses == 0 else 100 - (100 / (1 + (gains / losses)))
    return np.array(
        [
            (history[-1] / history[-2]) - 1,
            (history[-1] / history[-6]) - 1,
            (history[-1] / sma_5) - 1,
            (history[-1] / sma_20) - 1,
            returns[-20:].std(ddof=0),
            volumes[-1] / max(volumes[-20:].mean(), 1.0),
            rsi / 100.0,
        ],
        dtype=float,
    )
