"""models 파일은 백엔드 도메인 기능을 담당한다."""

from dataclasses import dataclass


SCORE_AXES = ("technical", "financial", "news", "disclosure", "investor_flow", "market_risk")


@dataclass(frozen=True)
class AxisScore:
    """`AxisScore` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    axis: str
    label: str
    score: float | None
    weight: float
    available: bool
    evidence: list[str]


@dataclass(frozen=True)
class ScoreResult:
    """계산 또는 처리 결과를 묶어 전달하는 값 객체입니다."""

    engine_version: str
    weight_version: str
    validation_status: str
    overall_score: float
    coverage_ratio: float
    is_partial: bool
    reference_signal: str
    axes: list[AxisScore]
