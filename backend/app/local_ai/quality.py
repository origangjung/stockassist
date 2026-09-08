"""quality 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from dataclasses import dataclass

from app.local_ai.contracts import ModelName


MINIMUM_VALIDATION_SAMPLES: dict[ModelName, int] = {
    "technical": 200,
    "financial": 200,
    "news": 200,
    "investor_flow": 200,
    "risk": 200,
    "synthesis": 1_000,
    "etf_technical": 1_000,
    "etf_risk": 1_000,
    "etf_synthesis": 1_000,
}


@dataclass(frozen=True)
class QualityAssessment:
    """`QualityAssessment` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    accepted: bool
    reasons: tuple[str, ...]


def assess_model_quality(
    model: ModelName, metrics: dict[str, float]
) -> QualityAssessment:
    """`assess_model_quality`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    accuracy = float(metrics.get("accuracy", 0.0))
    balanced = float(metrics.get("balanced_accuracy", accuracy))
    brier = float(metrics.get("brier_score", 1.0))
    calibration_error = float(metrics.get("calibration_error", 1.0))
    validation_samples = int(metrics.get("validation_samples", 0))
    positive_rate = float(metrics.get("positive_rate", 0.5))
    baseline = float(
        metrics.get("baseline_accuracy", max(positive_rate, 1.0 - positive_rate))
    )
    improvement = float(
        metrics.get("baseline_improvement", accuracy - baseline)
    )
    roc_auc = float(metrics.get("roc_auc", 0.5))
    minimum_accuracy = 0.55 if model in ("synthesis", "etf_synthesis") else 0.5
    minimum_balanced = 0.52 if model == "etf_technical" else 0.5

    reasons = []
    if accuracy < minimum_accuracy:
        reasons.append(f"accuracy<{minimum_accuracy:.2f}")
    if balanced <= minimum_balanced:
        reasons.append(f"balanced_accuracy<={minimum_balanced:.2f}")
    if brier >= 0.25:
        reasons.append("brier_score>=0.25")
    if calibration_error > 0.10:
        reasons.append("calibration_error>0.10")
    if validation_samples < MINIMUM_VALIDATION_SAMPLES[model]:
        reasons.append(
            f"validation_samples<{MINIMUM_VALIDATION_SAMPLES[model]}"
        )
    if improvement <= 0.0:
        reasons.append("baseline_improvement<=0")
    if roc_auc <= 0.5:
        reasons.append("roc_auc<=0.50")
    return QualityAssessment(not reasons, tuple(reasons))


def quality_evidence(metrics: dict[str, float], assessment: QualityAssessment) -> str:
    """`quality_evidence`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return (
        "quality_gate_failed "
        f"accuracy={float(metrics.get('accuracy', 0.0)):.4f} "
        f"baseline={float(metrics.get('baseline_accuracy', 0.0)):.4f} "
        f"improvement={float(metrics.get('baseline_improvement', 0.0)):.4f} "
        f"balanced_accuracy={float(metrics.get('balanced_accuracy', 0.0)):.4f} "
        f"roc_auc={float(metrics.get('roc_auc', 0.5)):.4f} "
        f"brier_score={float(metrics.get('brier_score', 1.0)):.4f} "
        f"calibration_error={float(metrics.get('calibration_error', 1.0)):.4f} "
        f"validation_samples={int(metrics.get('validation_samples', 0))} "
        f"reasons={','.join(assessment.reasons)}"
    )
