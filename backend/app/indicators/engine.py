from dataclasses import asdict
from math import isfinite
from typing import Any

import numpy as np
import pandas as pd

from app.providers.contracts import Candle


ENGINE_VERSION = "technical-2026.1"


def _wilder_smoothing(values: pd.Series, period: int) -> pd.Series:
    """Wilder RMA seeded by the first complete simple average."""
    result = pd.Series(np.nan, index=values.index, dtype="float64")
    valid: list[float] = []
    average: float | None = None
    for position, value in enumerate(values.astype(float)):
        if np.isnan(value):
            continue
        if average is None:
            valid.append(value)
            if len(valid) == period:
                average = sum(valid) / period
                result.iloc[position] = average
        else:
            average = ((average * (period - 1)) + value) / period
            result.iloc[position] = average
    return result


def _safe_value(value: Any) -> float | int | str | bool | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return round(number, 6) if isfinite(number) else None
    return value


class IndicatorEngine:
    """Pure calculation engine. It never fetches data or produces trading instructions."""

    version = ENGINE_VERSION
    status = "experimental"

    def calculate(self, candles: list[Candle]) -> list[dict[str, Any]]:
        if not candles:
            return []
        frame = (
            pd.DataFrame([asdict(candle) for candle in candles])
            .sort_values("timestamp")
            .reset_index(drop=True)
        )
        for column in ("open", "high", "low", "close"):
            frame[column] = frame[column].astype(float)
        frame["volume"] = frame["volume"].astype(float)

        close, high, low, volume = frame["close"], frame["high"], frame["low"], frame["volume"]
        frame["ma_5"] = close.rolling(5).mean()
        frame["ma_20"] = close.rolling(20).mean()

        delta = close.diff()
        average_gain = _wilder_smoothing(delta.clip(lower=0), 14)
        average_loss = _wilder_smoothing((-delta.clip(upper=0)), 14)
        relative_strength = average_gain / average_loss.replace(0, np.nan)
        frame["rsi_14"] = 100 - (100 / (1 + relative_strength))
        frame.loc[(average_loss == 0) & average_gain.notna(), "rsi_14"] = 100.0

        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        frame["macd"] = ema_12 - ema_26
        frame["macd_signal"] = frame["macd"].ewm(span=9, adjust=False).mean()
        frame["macd_histogram"] = frame["macd"] - frame["macd_signal"]

        middle = close.rolling(20).mean()
        deviation = close.rolling(20).std(ddof=0)
        frame["bb_middle"] = middle
        frame["bb_upper"] = middle + (2 * deviation)
        frame["bb_lower"] = middle - (2 * deviation)

        previous_close = close.shift(1)
        true_range = pd.concat(
            [high - low, (high - previous_close).abs(), (low - previous_close).abs()], axis=1
        ).max(axis=1)
        frame["atr_14"] = _wilder_smoothing(true_range, 14)

        up_move, down_move = high.diff(), -low.diff()
        plus_dm = pd.Series(
            np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=frame.index
        )
        minus_dm = pd.Series(
            np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=frame.index
        )
        smoothed_tr = _wilder_smoothing(true_range, 14)
        plus_di = 100 * _wilder_smoothing(plus_dm, 14) / smoothed_tr
        minus_di = 100 * _wilder_smoothing(minus_dm, 14) / smoothed_tr
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        frame["plus_di_14"], frame["minus_di_14"] = plus_di, minus_di
        frame["adx_14"] = _wilder_smoothing(dx, 14)

        typical = (high + low + close) / 3
        raw_money_flow = typical * volume
        direction = typical.diff()
        positive_flow = raw_money_flow.where(direction > 0, 0.0)
        negative_flow = raw_money_flow.where(direction < 0, 0.0)
        money_ratio = positive_flow.rolling(14).sum() / negative_flow.rolling(14).sum().replace(
            0, np.nan
        )
        frame["mfi_14"] = 100 - (100 / (1 + money_ratio))
        frame.loc[
            (negative_flow.rolling(14).sum() == 0) & (positive_flow.rolling(14).sum() > 0), "mfi_14"
        ] = 100.0

        cumulative_volume = volume.cumsum().replace(0, np.nan)
        frame["vwap"] = (typical * volume).cumsum() / cumulative_volume
        frame["obv"] = (np.sign(close.diff()).fillna(0) * volume).cumsum()

        supertrend, direction_series = self._supertrend(high, low, close, period=10, multiplier=3.0)
        frame["supertrend_10_3"] = supertrend
        frame["supertrend_direction"] = direction_series

        output_columns = [
            "timestamp",
            "ma_5",
            "ma_20",
            "rsi_14",
            "macd",
            "macd_signal",
            "macd_histogram",
            "bb_middle",
            "bb_upper",
            "bb_lower",
            "atr_14",
            "plus_di_14",
            "minus_di_14",
            "adx_14",
            "mfi_14",
            "vwap",
            "obv",
            "supertrend_10_3",
            "supertrend_direction",
        ]
        rows: list[dict[str, Any]] = []
        for record in frame[output_columns].to_dict(orient="records"):
            record["timestamp"] = record["timestamp"].isoformat()
            rows.append({key: _safe_value(value) for key, value in record.items()})
        return rows

    @staticmethod
    def _supertrend(
        high: pd.Series, low: pd.Series, close: pd.Series, period: int, multiplier: float
    ) -> tuple[pd.Series, pd.Series]:
        true_range = pd.concat(
            [high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1
        ).max(axis=1)
        atr = _wilder_smoothing(true_range, period)
        midpoint = (high + low) / 2
        upper, lower = midpoint + multiplier * atr, midpoint - multiplier * atr
        final_upper, final_lower = upper.copy(), lower.copy()
        trend = pd.Series(np.nan, index=close.index, dtype="float64")
        direction = pd.Series(0, index=close.index, dtype="int64")
        for index in range(1, len(close)):
            if pd.isna(atr.iloc[index]):
                continue
            previous = index - 1
            if (
                pd.notna(final_upper.iloc[previous])
                and close.iloc[previous] <= final_upper.iloc[previous]
            ):
                final_upper.iloc[index] = min(upper.iloc[index], final_upper.iloc[previous])
            if (
                pd.notna(final_lower.iloc[previous])
                and close.iloc[previous] >= final_lower.iloc[previous]
            ):
                final_lower.iloc[index] = max(lower.iloc[index], final_lower.iloc[previous])
            if direction.iloc[previous] == 0:
                direction.iloc[index] = 1 if close.iloc[index] >= midpoint.iloc[index] else -1
            elif direction.iloc[previous] == 1:
                direction.iloc[index] = -1 if close.iloc[index] < final_lower.iloc[index] else 1
            else:
                direction.iloc[index] = 1 if close.iloc[index] > final_upper.iloc[index] else -1
            trend.iloc[index] = (
                final_lower.iloc[index] if direction.iloc[index] == 1 else final_upper.iloc[index]
            )
        return trend, direction.replace(0, np.nan)
