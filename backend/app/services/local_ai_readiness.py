"""직접 학습 AI artifact의 운영 준비도를 안전하게 요약한다.

관리자 화면에는 모델 계수나 로컬 경로를 노출하지 않고, 체크섬 검증을 통과한
artifact의 검증 지표와 품질 게이트 결과만 전달한다.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Final

from app.local_ai.contracts import ModelName
from app.local_ai.model import LocalLogisticModel
from app.local_ai.quality import MINIMUM_VALIDATION_SAMPLES, assess_model_quality


MODEL_FILES: Final[tuple[tuple[ModelName, str, str], ...]] = (
    ("technical", "technical.json", "기술 분석"),
    ("financial", "financial.json", "재무 분석"),
    ("news", "news.json", "뉴스·공시"),
    ("investor_flow", "investor_flow.json", "수급 분석"),
    ("risk", "risk.json", "위험 분석"),
    ("synthesis", "synthesis.json", "종합 판단"),
    ("etf_technical", "etf_technical.json", "ETF 기술 분석"),
    ("etf_risk", "etf_risk.json", "ETF 위험 분석"),
)

METRIC_KEYS: Final[tuple[str, ...]] = (
    "accuracy",
    "baseline_accuracy",
    "baseline_improvement",
    "balanced_accuracy",
    "roc_auc",
    "brier_score",
    "calibration_error",
    "positive_rate",
    "validation_samples",
)


class LocalAiReadinessService:
    """로컬 AI 파일을 검증하고 관리자용 준비도 요약을 생성한다."""

    def __init__(self, artifact_dir: str | Path, *, enabled: bool) -> None:
        """허용된 artifact 루트와 런타임 활성화 상태를 저장한다."""

        self._artifact_dir = Path(artifact_dir).expanduser().resolve()
        self._enabled = enabled

    def summary(self) -> dict[str, object]:
        """모델별 품질 상태와 전체 준비도 통계를 반환한다."""

        items = [self._inspect_model(*definition) for definition in MODEL_FILES]
        status_counts = {
            status: sum(item["status"] == status for item in items)
            for status in ("available", "quality_rejected", "missing", "artifact_invalid")
        }
        core_items = [item for item in items if item["scope"] == "core"]
        return {
            "enabled": self._enabled,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total": len(items),
                "available": status_counts["available"],
                "quality_rejected": status_counts["quality_rejected"],
                "missing": status_counts["missing"],
                "artifact_invalid": status_counts["artifact_invalid"],
                "core_ready": all(item["status"] == "available" for item in core_items),
            },
            "items": items,
        }

    def _inspect_model(
        self,
        model: ModelName,
        filename: str,
        label: str,
    ) -> dict[str, object]:
        """고정 파일 하나를 체크섬과 품질 기준으로 검사한다."""

        path = self._artifact_dir / filename
        scope = "etf" if model.startswith("etf_") else "core"
        if not path.is_file():
            return self._empty_item(model, label, scope, "missing", ("artifact_missing",))

        try:
            artifact = LocalLogisticModel.load(path, expected_agent=model).artifact
        except (OSError, ValueError):
            return self._empty_item(
                model,
                label,
                scope,
                "artifact_invalid",
                ("artifact_integrity_check_failed",),
            )

        assessment = assess_model_quality(model, artifact.metrics)
        metrics = {
            key: float(artifact.metrics[key])
            for key in METRIC_KEYS
            if key in artifact.metrics
        }
        validation_samples = int(metrics.get("validation_samples", 0))
        required_samples = MINIMUM_VALIDATION_SAMPLES[model]
        return {
            "agent": model,
            "label": label,
            "scope": scope,
            "status": "available" if assessment.accepted else "quality_rejected",
            "model_version": artifact.model_version,
            "trained_at": artifact.trained_at,
            "training_samples": artifact.training_samples,
            "validation_samples": validation_samples,
            "required_validation_samples": required_samples,
            "remaining_validation_samples": max(0, required_samples - validation_samples),
            "metrics": metrics,
            "reasons": list(assessment.reasons),
        }

    @staticmethod
    def _empty_item(
        model: ModelName,
        label: str,
        scope: str,
        status: str,
        reasons: tuple[str, ...],
    ) -> dict[str, object]:
        """파일이 없거나 무효일 때 동일한 응답 계약을 만든다."""

        return {
            "agent": model,
            "label": label,
            "scope": scope,
            "status": status,
            "model_version": None,
            "trained_at": None,
            "training_samples": 0,
            "validation_samples": 0,
            "required_validation_samples": MINIMUM_VALIDATION_SAMPLES[model],
            "remaining_validation_samples": MINIMUM_VALIDATION_SAMPLES[model],
            "metrics": {},
            "reasons": list(reasons),
        }
