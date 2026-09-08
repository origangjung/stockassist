"""diagnostic 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from hmac import compare_digest

from app.local_ai.contracts import AgentName


SIGNAL_BANDS: dict[AgentName, float] = {
    "technical": 0.10,
    "financial": 0.10,
    "news": 0.125,
    "investor_flow": 0.225,
    "risk": 0.175,
}
DIAGNOSTIC_WEIGHTS: dict[AgentName, float] = {
    "technical": 0.30,
    "risk": 0.25,
    "investor_flow": 0.20,
    "financial": 0.15,
    "news": 0.10,
}
DIAGNOSTIC_SIGNAL_THRESHOLD = 0.20
RULE_SYNTHESIS_VERSION = "rule-based-diagnostic-v1"


@dataclass(frozen=True)
class DiagnosticCalculation:
    """`DiagnosticCalculation` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    signal: str
    score: float
    confidence: float
    disagreement: float
    included: tuple[tuple[str, float, float], ...]


@dataclass(frozen=True)
class DiagnosticPolicy:
    """`DiagnosticPolicy` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    approved: bool
    specialists: tuple[AgentName, ...]
    metrics: dict[str, float]


def load_diagnostic_policy(path: Path) -> DiagnosticPolicy:
    """`load_diagnostic_policy`은(는) 필요한 데이터를 조회해 반환합니다."""

    if not path.is_file() or path.is_symlink() or path.stat().st_size > 64 * 1024:
        raise ValueError("diagnostic validation policy is missing or invalid")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("diagnostic validation policy must be an object")
    supplied = str(payload.get("content_sha256") or "")
    unsigned = {key: value for key, value in payload.items() if key != "content_sha256"}
    encoded = json.dumps(
        unsigned, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode()
    if not compare_digest(supplied, sha256(encoded).hexdigest()):
        raise ValueError("diagnostic validation policy checksum is invalid")
    specialists = payload.get("specialists")
    metrics = payload.get("metrics")
    if (
        payload.get("schema_version") != 1
        or payload.get("version") != RULE_SYNTHESIS_VERSION
        or not isinstance(payload.get("approved"), bool)
        or not isinstance(specialists, list)
        or len(specialists) < 2
        or len(set(specialists)) != len(specialists)
        or any(name not in DIAGNOSTIC_WEIGHTS for name in specialists)
        or not isinstance(metrics, dict)
        or any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            for value in metrics.values()
        )
    ):
        raise ValueError("diagnostic validation policy schema is invalid")
    return DiagnosticPolicy(
        approved=payload["approved"],
        specialists=tuple(specialists),
        metrics={key: float(value) for key, value in metrics.items()},
    )


def directional_signal(agent: AgentName, probability: float) -> str:
    """`directional_signal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    band = SIGNAL_BANDS[agent]
    adverse_target = agent in ("investor_flow", "risk")
    if probability >= 0.5 + band:
        return "negative" if adverse_target else "positive"
    if probability <= 0.5 - band:
        return "positive" if adverse_target else "negative"
    return "neutral"


def calculate_diagnostic(
    results: dict[str, dict], specialist_names: tuple[AgentName, ...]
) -> DiagnosticCalculation | None:
    """`calculate_diagnostic`은(는) 입력 데이터를 기준으로 모델 또는 규칙의 결과 값을 계산해 반환합니다."""

    weighted = []
    for name in specialist_names:
        result = results.get(name) or {}
        if result.get("status") != "available":
            continue
        signal_value = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}.get(
            result.get("signal")
        )
        confidence = result.get("confidence")
        if signal_value is None or confidence is None:
            continue
        weighted.append(
            (
                name,
                signal_value,
                DIAGNOSTIC_WEIGHTS[name]
                * max(0.0, min(float(confidence), 1.0)),
            )
        )
    total_weight = sum(item[2] for item in weighted)
    if len(weighted) < 2 or total_weight <= 0:
        return None
    raw_score = sum(value * weight for _, value, weight in weighted) / total_weight
    signal = (
        "positive"
        if raw_score >= DIAGNOSTIC_SIGNAL_THRESHOLD
        else "negative"
        if raw_score <= -DIAGNOSTIC_SIGNAL_THRESHOLD
        else "neutral"
    )
    disagreement = diagnostic_disagreement(weighted)
    base_weight = sum(DIAGNOSTIC_WEIGHTS[name] for name, _, _ in weighted)
    mean_confidence = total_weight / max(base_weight, 1e-9)
    coverage = len(weighted) / len(specialist_names)
    return DiagnosticCalculation(
        signal=signal,
        score=round(50.0 + raw_score * 50.0, 2),
        confidence=round(
            coverage * mean_confidence * (1.0 - 0.5 * disagreement), 6
        ),
        disagreement=disagreement,
        included=tuple(weighted),
    )


def diagnostic_disagreement(weighted: list[tuple[str, float, float]]) -> float:
    """`diagnostic_disagreement`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    signed_weights = [direction * weight for _, direction, weight in weighted]
    positive = sum(value for value in signed_weights if value > 0)
    negative = -sum(value for value in signed_weights if value < 0)
    directional = positive + negative
    return round(2 * min(positive, negative) / directional, 6) if directional else 0.0
