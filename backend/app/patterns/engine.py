from dataclasses import asdict
from typing import Any

from app.patterns.models import DetectedPattern, PatternAnalysis
from app.providers.contracts import Candle


ENGINE_VERSION = "patterns-2026.1"


class PatternEngine:
    """Pure pattern detector using only candles available at the analysis timestamp."""

    version = ENGINE_VERSION
    status = "experimental"

    def analyze(self, candles: list[Candle]) -> dict[str, Any]:
        ordered = sorted(candles, key=lambda candle: candle.timestamp)
        if not ordered:
            return asdict(PatternAnalysis(self.version, self.status, None, 0, []))
        self._validate(ordered)
        patterns = [
            *self._latest_candlestick_patterns(ordered),
            *self._breakout_patterns(ordered),
            *self._reversal_patterns(ordered[-60:]),
        ]
        patterns.sort(key=lambda pattern: (-pattern.confidence, pattern.name))
        return asdict(
            PatternAnalysis(
                self.version,
                self.status,
                ordered[-1].timestamp,
                len(ordered),
                patterns,
            )
        )

    @staticmethod
    def _validate(candles: list[Candle]) -> None:
        for candle in candles:
            low, high = float(candle.low), float(candle.high)
            open_price, close = float(candle.open), float(candle.close)
            if high < low or not low <= open_price <= high or not low <= close <= high:
                raise ValueError("invalid OHLC candle supplied to PatternEngine")

    def _latest_candlestick_patterns(self, candles: list[Candle]) -> list[DetectedPattern]:
        latest = candles[-1]
        open_price, high = float(latest.open), float(latest.high)
        low, close = float(latest.low), float(latest.close)
        price_range = high - low
        if price_range <= 0:
            return []
        body = abs(close - open_price)
        upper_shadow = high - max(open_price, close)
        lower_shadow = min(open_price, close) - low
        body_ratio = body / price_range
        patterns: list[DetectedPattern] = []

        if body_ratio <= 0.10:
            patterns.append(
                self._pattern(
                    "candlestick",
                    "doji",
                    "neutral",
                    0.68,
                    latest,
                    latest,
                    [f"body/range={body_ratio:.3f}"],
                )
            )

        effective_body = max(body, price_range * 0.02)
        if (
            0.05 <= body_ratio <= 0.35
            and lower_shadow >= effective_body * 2
            and upper_shadow <= effective_body
            and max(open_price, close) >= low + price_range * 0.60
        ):
            patterns.append(
                self._pattern(
                    "candlestick",
                    "hammer",
                    "upward",
                    0.72,
                    latest,
                    latest,
                    [
                        f"lower_shadow/body={lower_shadow / effective_body:.2f}",
                        f"body/range={body_ratio:.3f}",
                    ],
                )
            )
        if (
            0.05 <= body_ratio <= 0.35
            and upper_shadow >= effective_body * 2
            and lower_shadow <= effective_body
            and min(open_price, close) <= low + price_range * 0.40
        ):
            patterns.append(
                self._pattern(
                    "candlestick",
                    "shooting_star",
                    "downward",
                    0.72,
                    latest,
                    latest,
                    [
                        f"upper_shadow/body={upper_shadow / effective_body:.2f}",
                        f"body/range={body_ratio:.3f}",
                    ],
                )
            )

        if len(candles) >= 2:
            previous = candles[-2]
            previous_open, previous_close = float(previous.open), float(previous.close)
            if (
                previous_close < previous_open
                and close > open_price
                and open_price <= previous_close
                and close >= previous_open
            ):
                patterns.append(
                    self._pattern(
                        "candlestick",
                        "bullish_engulfing",
                        "upward",
                        0.78,
                        previous,
                        latest,
                        ["current real body contains the previous bearish real body"],
                    )
                )
            if (
                previous_close > previous_open
                and close < open_price
                and open_price >= previous_close
                and close <= previous_open
            ):
                patterns.append(
                    self._pattern(
                        "candlestick",
                        "bearish_engulfing",
                        "downward",
                        0.78,
                        previous,
                        latest,
                        ["current real body contains the previous bullish real body"],
                    )
                )
        return patterns

    def _breakout_patterns(self, candles: list[Candle]) -> list[DetectedPattern]:
        if len(candles) < 21:
            return []
        previous = candles[-21:-1]
        latest = candles[-1]
        upper = max(float(candle.high) for candle in previous)
        lower = min(float(candle.low) for candle in previous)
        close = float(latest.close)
        span = max(upper - lower, abs(close) * 0.001)
        if close > upper:
            confidence = min(0.90, 0.68 + ((close - upper) / span) * 2)
            return [
                self._pattern(
                    "chart",
                    "range_breakout_up",
                    "upward",
                    confidence,
                    previous[0],
                    latest,
                    [f"close={close:.4f} above prior_20_high={upper:.4f}"],
                )
            ]
        if close < lower:
            confidence = min(0.90, 0.68 + ((lower - close) / span) * 2)
            return [
                self._pattern(
                    "chart",
                    "range_breakout_down",
                    "downward",
                    confidence,
                    previous[0],
                    latest,
                    [f"close={close:.4f} below prior_20_low={lower:.4f}"],
                )
            ]
        return []

    def _reversal_patterns(self, candles: list[Candle]) -> list[DetectedPattern]:
        if len(candles) < 12:
            return []
        patterns: list[DetectedPattern] = []
        double_top = self._confirmed_double(candles, top=True)
        double_bottom = self._confirmed_double(candles, top=False)
        if double_top is not None:
            patterns.append(double_top)
        if double_bottom is not None:
            patterns.append(double_bottom)
        return patterns

    def _confirmed_double(self, candles: list[Candle], *, top: bool) -> DetectedPattern | None:
        extrema = self._local_extrema(candles, top=top)
        latest_close = float(candles[-1].close)
        for right_position in range(len(extrema) - 1, 0, -1):
            for left_position in range(right_position - 1, -1, -1):
                left, right = extrema[left_position], extrema[right_position]
                separation = right - left
                if separation < 5 or separation > 35:
                    continue
                left_price = self._extreme_price(candles[left], top=top)
                right_price = self._extreme_price(candles[right], top=top)
                average_price = (left_price + right_price) / 2
                if average_price <= 0:
                    continue
                difference = abs(left_price - right_price) / average_price
                if difference > 0.03:
                    continue
                middle = candles[left + 1 : right]
                if not middle:
                    continue
                neckline = (
                    min(float(candle.low) for candle in middle)
                    if top
                    else max(float(candle.high) for candle in middle)
                )
                confirmed = latest_close < neckline if top else latest_close > neckline
                if not confirmed or right >= len(candles) - 1:
                    continue
                confidence = min(0.90, 0.76 + (0.03 - difference) * 3)
                name = "double_top_confirmed" if top else "double_bottom_confirmed"
                direction = "downward" if top else "upward"
                relation = "below" if top else "above"
                return self._pattern(
                    "chart",
                    name,
                    direction,
                    confidence,
                    candles[left],
                    candles[-1],
                    [
                        f"extreme_similarity={1 - difference:.3f}",
                        f"latest close confirmed {relation} neckline={neckline:.4f}",
                    ],
                )
        return None

    @staticmethod
    def _local_extrema(candles: list[Candle], *, top: bool) -> list[int]:
        extrema: list[int] = []
        prices = [PatternEngine._extreme_price(candle, top=top) for candle in candles]
        for index in range(2, len(prices) - 2):
            neighbors = prices[index - 2 : index] + prices[index + 1 : index + 3]
            if (top and prices[index] >= max(neighbors)) or (
                not top and prices[index] <= min(neighbors)
            ):
                extrema.append(index)
        return extrema

    @staticmethod
    def _extreme_price(candle: Candle, *, top: bool) -> float:
        return float(candle.high if top else candle.low)

    @staticmethod
    def _pattern(
        category: str,
        name: str,
        direction: str,
        confidence: float,
        first: Candle,
        last: Candle,
        evidence: list[str],
    ) -> DetectedPattern:
        return DetectedPattern(
            category,
            name,
            direction,
            round(confidence, 4),
            first.timestamp,
            last.timestamp,
            evidence,
        )
