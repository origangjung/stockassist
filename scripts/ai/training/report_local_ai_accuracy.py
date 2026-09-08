"""Report chronological validation quality for production local-AI artifacts."""

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.contracts import ModelName  # noqa: E402
from app.local_ai.model import LocalLogisticModel  # noqa: E402
from app.local_ai.quality import assess_model_quality  # noqa: E402


CORE_MODELS: tuple[ModelName, ...] = (
    "technical",
    "financial",
    "news",
    "investor_flow",
    "risk",
    "synthesis",
)
ETF_MODELS: tuple[ModelName, ...] = (
    "etf_technical",
    "etf_risk",
    "etf_synthesis",
)


@dataclass(frozen=True)
class QualityRow:
    """`QualityRow` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    model: str
    version: str | None
    training_samples: int
    validation_samples: int
    accuracy: float | None
    accuracy_ci_low: float | None
    accuracy_ci_high: float | None
    balanced_accuracy: float | None
    brier_score: float | None
    calibration_error: float | None
    baseline_accuracy: float | None
    baseline_improvement: float | None
    roc_auc: float | None
    status: str


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description="Report local-AI model quality")
    parser.add_argument(
        "--artifact-dir", type=Path, default=ROOT / "artifacts" / "local-ai"
    )
    parser.add_argument("--include-etf", action="store_true")
    parser.add_argument("--agent", choices=[*CORE_MODELS, *ETF_MODELS])
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def selected_models(agent: ModelName | None, include_etf: bool) -> tuple[ModelName, ...]:
    """단일 후보 또는 기본 운영 모델군 중 보고할 범위를 선택한다."""

    if agent is not None:
        return (agent,)
    return (*CORE_MODELS, *ETF_MODELS) if include_etf else CORE_MODELS


def wilson_interval(success_rate: float, samples: int) -> tuple[float, float]:
    """`wilson_interval`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if samples <= 0 or not 0.0 <= success_rate <= 1.0:
        raise ValueError("success rate or sample count is invalid")
    z = 1.959963984540054
    denominator = 1 + z * z / samples
    center = (success_rate + z * z / (2 * samples)) / denominator
    margin = (
        z
        * math.sqrt(
            success_rate * (1 - success_rate) / samples
            + z * z / (4 * samples * samples)
        )
        / denominator
    )
    return center - margin, center + margin


def quality_status(model: ModelName, metrics: dict[str, float]) -> str:
    """`quality_status`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return (
        "available"
        if assess_model_quality(model, metrics).accepted
        else "quality_rejected"
    )


def read_quality(artifact_dir: Path, model: ModelName) -> QualityRow:
    """`read_quality`은(는) 필요한 데이터를 조회해 반환합니다."""

    path = artifact_dir / f"{model}.json"
    if not path.is_file():
        return QualityRow(
            model, None, 0, 0, None, None, None, None, None, None, None, None, None,
            "missing",
        )
    try:
        artifact = LocalLogisticModel.load(path, expected_agent=model).artifact
    except ValueError:
        return QualityRow(
            model, None, 0, 0, None, None, None, None, None, None, None, None, None,
            "invalid",
        )
    metrics = artifact.metrics
    accuracy = float(metrics["accuracy"])
    validation_samples = int(metrics["validation_samples"])
    low, high = wilson_interval(accuracy, validation_samples)
    return QualityRow(
        model=model,
        version=artifact.model_version,
        training_samples=artifact.training_samples,
        validation_samples=validation_samples,
        accuracy=accuracy,
        accuracy_ci_low=round(low, 4),
        accuracy_ci_high=round(high, 4),
        balanced_accuracy=float(metrics["balanced_accuracy"]),
        brier_score=float(metrics["brier_score"]),
        calibration_error=float(metrics.get("calibration_error", 1.0)),
        baseline_accuracy=float(metrics.get("baseline_accuracy", 0.0)),
        baseline_improvement=float(metrics.get("baseline_improvement", 0.0)),
        roc_auc=float(metrics.get("roc_auc", 0.5)),
        status=quality_status(model, metrics),
    )


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    models = selected_models(args.agent, args.include_etf)
    rows = [read_quality(args.artifact_dir.resolve(), model) for model in models]
    if args.json:
        print(json.dumps([asdict(row) for row in rows], ensure_ascii=True, indent=2))
        return 0
    print(
        "model             accuracy  baseline  improve  balanced  auc     brier   ece     "
        "validation  status"
    )
    for row in rows:
        if row.accuracy is None:
            print(
                f"{row.model:17} {'-':8}  {'-':8}  {'-':7}  {'-':8}  {'-':6}  "
                f"{'-':6}  {'-':6}  {'-':10}  {row.status}"
            )
            continue
        print(
            f"{row.model:17} {row.accuracy:.4f}    "
            f"{row.baseline_accuracy:.4f}    {row.baseline_improvement:+.4f}  "
            f"{row.balanced_accuracy:.4f}    {row.roc_auc:.4f}  "
            f"{row.brier_score:.4f}  {row.calibration_error:.4f}  "
            f"{row.validation_samples:<10}  {row.status}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
