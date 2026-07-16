from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ReferenceSignalResult:
    signal: str
    strength: float
    basis: list[str]


def derive_reference_signal(
    score: dict | None,
    prediction: dict | None,
    warnings: list[dict],
) -> ReferenceSignalResult:
    """Combine calculated facts into an experimental, non-directive reference signal."""
    if warnings:
        return ReferenceSignalResult(
            signal="risk_aware",
            strength=100.0,
            basis=[f"Provider data contains {len(warnings)} active market warning signal(s)."],
        )

    overall_score = _number(score, "overall_score")
    rise_probability = _number(prediction, "rise_probability")
    if overall_score is None or rise_probability is None:
        return ReferenceSignalResult(
            signal="data_insufficient",
            strength=0.0,
            basis=["Score or prediction output is unavailable."],
        )

    score_component = (overall_score - 50.0) / 50.0
    prediction_component = (rise_probability - 0.5) * 2.0
    consensus = max(-1.0, min(1.0, score_component * 0.55 + prediction_component * 0.45))
    signal = (
        "positive_watch"
        if consensus >= 0.12
        else "defensive_watch"
        if consensus <= -0.12
        else "neutral_watch"
    )
    coverage = _number(score, "coverage_ratio")
    basis = [
        f"Score Engine output is {overall_score:.1f}/100.",
        f"Experimental rise probability is {rise_probability:.1%}.",
    ]
    if coverage is not None:
        basis.append(f"Available score-axis coverage is {coverage:.0%}.")
    return ReferenceSignalResult(
        signal=signal,
        strength=round(abs(consensus) * 100, 2),
        basis=basis,
    )


def _number(source: dict | None, key: str) -> float | None:
    if not isinstance(source, dict):
        return None
    value = source.get(key)
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    return None
