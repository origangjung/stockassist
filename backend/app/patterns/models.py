from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DetectedPattern:
    category: str
    name: str
    direction: str
    confidence: float
    started_at: datetime
    ended_at: datetime
    evidence: list[str]


@dataclass(frozen=True)
class PatternAnalysis:
    engine_version: str
    validation_status: str
    data_as_of: datetime | None
    window_size: int
    patterns: list[DetectedPattern]
