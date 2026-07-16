from dataclasses import dataclass
from math import tanh
from collections.abc import Mapping
from typing import Any

from app.providers.contracts import Candle
from app.score.models import AxisScore, SCORE_AXES, ScoreResult
from app.score.axes import AxisInput


ENGINE_VERSION = "score-2026.2"
AXIS_LABELS = {
    "technical": "기술적 분석",
    "financial": "재무",
    "news": "뉴스",
    "disclosure": "공시",
    "investor_flow": "수급",
    "market_risk": "시장 위험도",
}


@dataclass(frozen=True)
class ScoreWeights:
    version: str
    weights: dict[str, float]

    def __post_init__(self) -> None:
        if set(self.weights) != set(SCORE_AXES):
            raise ValueError("weights must define all six score axes")
        if any(value < 0 for value in self.weights.values()) or sum(self.weights.values()) <= 0:
            raise ValueError("weights must be non-negative with a positive total")


DEFAULT_WEIGHTS = ScoreWeights(
    version="weights-2026.1",
    weights={
        "technical": 0.30,
        "financial": 0.20,
        "news": 0.10,
        "disclosure": 0.10,
        "investor_flow": 0.15,
        "market_risk": 0.15,
    },
)


def _clamp(value: float, lower: float = 0, upper: float = 100) -> float:
    return max(lower, min(upper, value))


class TechnicalScoreCalculator:
    """Explainable technical score composed only from already calculated indicators."""

    def calculate(
        self, candle: Candle, indicators: dict[str, Any]
    ) -> tuple[float | None, list[str]]:
        components: list[float] = []
        evidence: list[str] = []
        close = float(candle.close)

        rsi = indicators.get("rsi_14")
        if rsi is not None:
            if 30 <= rsi <= 70:
                score = 50 + (rsi - 50) * 1.25
            elif rsi > 70:
                score = 75 - (rsi - 70) * 2
            else:
                score = 25 + (rsi / 30) * 12.5
            components.append(_clamp(score, 20, 80))
            evidence.append(f"RSI(14) {rsi:.1f}")

        histogram = indicators.get("macd_histogram")
        if histogram is not None and close > 0:
            components.append(50 + 30 * tanh(float(histogram) / (close * 0.005)))
            evidence.append(f"MACD histogram {histogram:.2f}")

        ma_5, ma_20 = indicators.get("ma_5"), indicators.get("ma_20")
        if ma_5 is not None and ma_20 is not None:
            if close > ma_5 > ma_20:
                components.append(80)
                evidence.append("종가 > MA5 > MA20")
            elif close < ma_5 < ma_20:
                components.append(20)
                evidence.append("종가 < MA5 < MA20")
            else:
                components.append(50)
                evidence.append("이동평균 혼조")

        adx, plus_di, minus_di = (
            indicators.get("adx_14"),
            indicators.get("plus_di_14"),
            indicators.get("minus_di_14"),
        )
        if adx is not None and plus_di is not None and minus_di is not None:
            if adx >= 25:
                components.append(75 if plus_di > minus_di else 25)
            else:
                components.append(50)
            evidence.append(f"ADX {adx:.1f}, +DI {plus_di:.1f}, -DI {minus_di:.1f}")

        mfi = indicators.get("mfi_14")
        if mfi is not None:
            components.append(65 if 45 <= mfi <= 70 else 35 if mfi > 80 or mfi < 20 else 50)
            evidence.append(f"MFI(14) {mfi:.1f}")

        supertrend = indicators.get("supertrend_direction")
        if supertrend is not None:
            components.append(70 if supertrend > 0 else 30)
            evidence.append("SuperTrend 상승" if supertrend > 0 else "SuperTrend 하락")

        if not components:
            return None, ["지표 warm-up 구간으로 계산 가능한 값이 없습니다."]
        return round(sum(components) / len(components), 4), evidence


class ScoreEngine:
    version = ENGINE_VERSION
    status = "experimental"

    def __init__(self, weights: ScoreWeights = DEFAULT_WEIGHTS):
        self.weights = weights

    def aggregate(
        self,
        technical: AxisInput,
        additional_inputs: Mapping[str, AxisInput] | None = None,
    ) -> ScoreResult:
        technical_score, technical_evidence = technical
        inputs = {"technical": (technical_score, technical_evidence)}
        if additional_inputs:
            inputs.update(
                (axis, value)
                for axis, value in additional_inputs.items()
                if axis in SCORE_AXES and axis != "technical"
            )
        axes: list[AxisScore] = []
        weighted_sum = 0.0
        available_weight = 0.0
        total_weight = sum(self.weights.weights.values())
        for axis in SCORE_AXES:
            score, evidence = inputs.get(
                axis, (None, ["해당 데이터 소스는 아직 연결되지 않았습니다."])
            )
            available = score is not None
            weight = self.weights.weights[axis]
            axes.append(AxisScore(axis, AXIS_LABELS[axis], score, weight, available, evidence))
            if available:
                weighted_sum += float(score) * weight
                available_weight += weight
        overall = weighted_sum / available_weight if available_weight else 50.0
        coverage = available_weight / total_weight
        signal = "긍정 관찰" if overall >= 65 else "위험 관찰" if overall <= 35 else "중립 관찰"
        return ScoreResult(
            engine_version=self.version,
            weight_version=self.weights.version,
            validation_status=self.status,
            overall_score=round(overall, 4),
            coverage_ratio=round(coverage, 4),
            is_partial=coverage < 1,
            reference_signal=signal,
            axes=axes,
        )
