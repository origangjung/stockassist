from dataclasses import dataclass


SCORE_AXES = ("technical", "financial", "news", "disclosure", "investor_flow", "market_risk")


@dataclass(frozen=True)
class AxisScore:
    axis: str
    label: str
    score: float | None
    weight: float
    available: bool
    evidence: list[str]


@dataclass(frozen=True)
class ScoreResult:
    engine_version: str
    weight_version: str
    validation_status: str
    overall_score: float
    coverage_ratio: float
    is_partial: bool
    reference_signal: str
    axes: list[AxisScore]
