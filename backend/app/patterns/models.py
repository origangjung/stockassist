"""models 파일은 백엔드 도메인 기능을 담당한다."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DetectedPattern:
    """`DetectedPattern` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    category: str
    name: str
    direction: str
    confidence: float
    started_at: datetime
    ended_at: datetime
    evidence: list[str]


@dataclass(frozen=True)
class PatternReferenceSignal:
    """워크포워드 검증을 통과한 약한 상대성과 참고 신호입니다."""

    pattern_name: str
    outlook: str
    horizon_days: int
    benchmark: str
    validation_accuracy: float
    validation_samples: int
    validation_status: str


@dataclass(frozen=True)
class PatternAnalysis:
    """`PatternAnalysis` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    engine_version: str
    validation_status: str
    data_as_of: datetime | None
    window_size: int
    patterns: list[DetectedPattern]
    reference_signals: list[PatternReferenceSignal]
