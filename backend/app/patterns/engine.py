"""engine 파일은 백엔드 도메인 기능을 담당한다."""

from dataclasses import asdict
from typing import Any

from app.patterns.models import DetectedPattern, PatternAnalysis, PatternReferenceSignal
from app.providers.contracts import Candle


ENGINE_VERSION = "patterns-2026.2"


class PatternEngine:
    """Pure pattern detector using only candles available at the analysis timestamp."""

    version = ENGINE_VERSION
    status = "experimental"

    def analyze(self, candles: list[Candle]) -> dict[str, Any]:
        """`analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다."""

        ordered = sorted(candles, key=lambda candle: candle.timestamp)
        if not ordered:
            return asdict(PatternAnalysis(self.version, self.status, None, 0, [], []))
        self._validate(ordered)
        patterns = [
            *self._latest_candlestick_patterns(ordered),
            *self._breakout_patterns(ordered),
            *self._reversal_patterns(ordered[-60:]),
            *self._consolidation_patterns(ordered[-30:]),
        ]
        patterns.sort(key=lambda pattern: (-pattern.confidence, pattern.name))
        return asdict(
            PatternAnalysis(
                self.version,
                self.status,
                ordered[-1].timestamp,
                len(ordered),
                patterns,
                self._reference_signals(patterns),
            )
        )

    @staticmethod
    def _reference_signals(
        patterns: list[DetectedPattern],
    ) -> list[PatternReferenceSignal]:
        """엄격한 워크포워드에서 반복 확인된 10일 상대 약세만 분리한다."""

        validated = {"double_top_confirmed", "head_and_shoulders_confirmed"}
        return [
            PatternReferenceSignal(
                pattern.name,
                "relative_underperformance_watch",
                10,
                "SPY",
                0.5257,
                4_390,
                "weak_walk_forward_validated",
            )
            for pattern in patterns
            if pattern.name in validated
        ]

    @staticmethod
    def _validate(candles: list[Candle]) -> None:
        """`_validate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        for candle in candles:
            low, high = float(candle.low), float(candle.high)
            open_price, close = float(candle.open), float(candle.close)
            if high < low or not low <= open_price <= high or not low <= close <= high:
                raise ValueError("invalid OHLC candle supplied to PatternEngine")

    def _latest_candlestick_patterns(self, candles: list[Candle]) -> list[DetectedPattern]:
        """`_latest_candlestick_patterns`은(는) 필요한 데이터를 조회해 반환합니다."""

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
        """`_breakout_patterns`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
        """`_reversal_patterns`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        if len(candles) < 12:
            return []
        patterns: list[DetectedPattern] = []
        double_top = self._confirmed_double(candles, top=True)
        double_bottom = self._confirmed_double(candles, top=False)
        if double_top is not None:
            patterns.append(double_top)
        if double_bottom is not None:
            patterns.append(double_bottom)
        head_shoulders = self._confirmed_head_shoulders(candles, inverse=False)
        inverse_head_shoulders = self._confirmed_head_shoulders(candles, inverse=True)
        if head_shoulders is not None:
            patterns.append(head_shoulders)
        if inverse_head_shoulders is not None:
            patterns.append(inverse_head_shoulders)
        return patterns

    def _confirmed_head_shoulders(
        self, candles: list[Candle], *, inverse: bool
    ) -> DetectedPattern | None:
        """세 극점과 목선 돌파가 모두 확인된 헤드앤숄더만 반환한다."""

        extrema = self._local_extrema(candles, top=not inverse)
        latest_close = float(candles[-1].close)
        for right_position in range(len(extrema) - 1, 1, -1):
            left, head, right = extrema[right_position - 2 : right_position + 1]
            if not (3 <= head - left <= 20 and 3 <= right - head <= 20):
                continue
            prices = [
                self._extreme_price(candles[index], top=not inverse)
                for index in (left, head, right)
            ]
            left_price, head_price, right_price = prices
            shoulder_average = (left_price + right_price) / 2
            if shoulder_average <= 0:
                continue
            shoulder_difference = abs(left_price - right_price) / shoulder_average
            head_gap = (
                (shoulder_average - head_price) / shoulder_average
                if inverse
                else (head_price - shoulder_average) / shoulder_average
            )
            if shoulder_difference > 0.05 or head_gap < 0.02:
                continue
            left_middle = candles[left + 1 : head]
            right_middle = candles[head + 1 : right]
            if not left_middle or not right_middle:
                continue
            left_neck = (
                max(float(candle.high) for candle in left_middle)
                if inverse
                else min(float(candle.low) for candle in left_middle)
            )
            right_neck = (
                max(float(candle.high) for candle in right_middle)
                if inverse
                else min(float(candle.low) for candle in right_middle)
            )
            neckline = (left_neck + right_neck) / 2
            confirmed = latest_close > neckline if inverse else latest_close < neckline
            if not confirmed or right >= len(candles) - 1:
                continue
            return self._pattern(
                "chart",
                "inverse_head_and_shoulders_confirmed"
                if inverse
                else "head_and_shoulders_confirmed",
                "upward" if inverse else "downward",
                min(0.92, 0.76 + head_gap + (0.05 - shoulder_difference)),
                candles[left],
                candles[-1],
                [
                    f"shoulder_similarity={1 - shoulder_difference:.3f}",
                    f"head_gap={head_gap:.3f}",
                    f"neckline={neckline:.4f} confirmed",
                ],
            )
        return None

    def _consolidation_patterns(self, candles: list[Candle]) -> list[DetectedPattern]:
        """최근 20봉의 고점·저점 추세선 기울기로 삼각수렴을 감지한다."""

        if len(candles) < 20:
            return []
        window = candles[-20:]
        x = list(range(len(window)))
        high_slope = self._linear_slope(x, [float(item.high) for item in window])
        low_slope = self._linear_slope(x, [float(item.low) for item in window])
        average_price = sum(float(item.close) for item in window) / len(window)
        if average_price <= 0:
            return []
        high_rate, low_rate = high_slope / average_price, low_slope / average_price
        initial_width = float(window[0].high) - float(window[0].low)
        final_width = float(window[-1].high) - float(window[-1].low)
        if initial_width <= 0 or final_width >= initial_width * 0.85:
            return []
        flat = 0.0007
        trend = 0.0008
        if high_rate <= -trend and low_rate >= trend:
            name, direction = "symmetrical_triangle", "neutral"
        elif abs(high_rate) <= flat and low_rate >= trend:
            name, direction = "ascending_triangle", "upward"
        elif high_rate <= -trend and abs(low_rate) <= flat:
            name, direction = "descending_triangle", "downward"
        else:
            return []
        convergence = 1.0 - final_width / initial_width
        return [
            self._pattern(
                "chart",
                name,
                direction,
                min(0.86, 0.62 + convergence * 0.3),
                window[0],
                window[-1],
                [
                    f"resistance_slope_rate={high_rate:.5f}",
                    f"support_slope_rate={low_rate:.5f}",
                    f"range_contraction={convergence:.3f}",
                ],
            )
        ]

    @staticmethod
    def _linear_slope(x: list[int], y: list[float]) -> float:
        """최소제곱 직선의 기울기를 외부 수치 라이브러리 없이 계산한다."""

        x_average, y_average = sum(x) / len(x), sum(y) / len(y)
        denominator = sum((value - x_average) ** 2 for value in x)
        return (
            sum((left - x_average) * (right - y_average) for left, right in zip(x, y))
            / denominator
            if denominator
            else 0.0
        )

    def _confirmed_double(self, candles: list[Candle], *, top: bool) -> DetectedPattern | None:
        """`_confirmed_double`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
        """`_local_extrema`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
        """`_extreme_price`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
        """`_pattern`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        return DetectedPattern(
            category,
            name,
            direction,
            round(confidence, 4),
            first.timestamp,
            last.timestamp,
            evidence,
        )
