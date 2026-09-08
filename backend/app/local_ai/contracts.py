"""contracts 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from dataclasses import asdict, dataclass
from typing import Literal


AgentName = Literal["technical", "financial", "news", "investor_flow", "risk"]
ModelName = Literal[
    "technical",
    "financial",
    "news",
    "investor_flow",
    "risk",
    "synthesis",
    "etf_technical",
    "etf_risk",
    "etf_synthesis",
]


@dataclass(frozen=True)
class LocalAgentResult:
    """계산 또는 처리 결과를 묶어 전달하는 값 객체입니다."""

    agent: AgentName
    target: str
    status: str
    signal: str | None
    probability: float | None
    confidence: float | None
    model_version: str | None
    evidence: list[str]
    horizon_days: int | None = None

    def to_dict(self) -> dict:
        """`to_dict`은(는) 내부 값을 전송·표시 가능한 형식으로 변환합니다."""

        return asdict(self)


@dataclass(frozen=True)
class LocalSynthesisResult:
    """계산 또는 처리 결과를 묶어 전달하는 값 객체입니다."""

    status: str
    target: str
    signal: str | None
    probability: float | None
    confidence: float | None
    model_version: str | None
    available_agents: int
    disagreement: float | None
    evidence: list[str]
    diagnostic_score: float | None = None

    def to_dict(self) -> dict:
        """`to_dict`은(는) 내부 값을 전송·표시 가능한 형식으로 변환합니다."""

        return asdict(self)
