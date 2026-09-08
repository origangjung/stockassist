"""기본 기술 회귀와 실적 이벤트 후보를 비교해 승격 가능성만 판정한다."""

import argparse
import json
import math
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = (ROOT / "artifacts").resolve()
EVENT_KEY = "subgroup:earnings_event_10d"


def parse_args() -> argparse.Namespace:
    """기본·후보 보고서와 출력 경로를 읽는다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum-event-samples", type=int, default=200)
    parser.add_argument("--minimum-event-direction-accuracy", type=float, default=0.55)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def _metric(report: dict[str, object], name: str) -> float:
    """필수 숫자 지표를 유한한 실수로 검증해 반환한다."""

    try:
        value = float(report["metrics"][name])  # type: ignore[index]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"missing metric: {name}") from exc
    if not math.isfinite(value):
        raise ValueError(f"non-finite metric: {name}")
    return value


def _event_metrics(report: dict[str, object]) -> dict[str, float]:
    """동일한 발표 후 10일 하위집단 지표를 검증한다."""

    try:
        raw = report["metrics"][EVENT_KEY]  # type: ignore[index]
        values = {
            name: float(raw[name])  # type: ignore[index]
            for name in (
                "samples",
                "mae",
                "zero_baseline_mae",
                "actionable_coverage",
                "actionable_direction_accuracy",
            )
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("event subgroup metrics are missing") from exc
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError("event subgroup metrics contain non-finite values")
    return values


def assess(
    base: dict[str, object],
    candidate: dict[str, object],
    *,
    minimum_event_samples: int = 200,
    minimum_event_direction_accuracy: float = 0.55,
) -> dict[str, object]:
    """전체·이벤트·구간 안정성 조건을 모두 적용해 후보를 판정한다."""

    if minimum_event_samples < 1 or not 0.5 <= minimum_event_direction_accuracy <= 1:
        raise ValueError("promotion thresholds are invalid")
    base_event = _event_metrics(base)
    candidate_event = _event_metrics(candidate)
    base_samples = int(_metric(base, "validation_samples"))
    candidate_samples = int(_metric(candidate, "validation_samples"))
    try:
        feature_counts = candidate["selected_feature_sets"]
        folds = candidate["folds"]
        extra_selected = sum(
            int(count)
            for name, count in feature_counts.items()  # type: ignore[union-attr]
            if str(name).startswith("extra:")
        )
        fold_count = len(folds)  # type: ignore[arg-type]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("candidate selection details are missing") from exc

    reasons: list[str] = []
    if base_samples != candidate_samples or base_samples <= 0:
        reasons.append("validation_samples_mismatch")
    if int(base_event["samples"]) != int(candidate_event["samples"]):
        reasons.append("event_samples_mismatch")
    if candidate_event["samples"] < minimum_event_samples:
        reasons.append("event_samples_below_minimum")
    if not bool(candidate.get("promotion_ready")):
        reasons.append("candidate_regression_gate_failed")
    if _metric(candidate, "mae") >= _metric(base, "mae"):
        reasons.append("overall_mae_not_improved")
    if _metric(candidate, "return_correlation") < _metric(base, "return_correlation"):
        reasons.append("return_correlation_worse")
    if _metric(candidate, "minimum_fold_mae_improvement") < 0:
        reasons.append("unstable_outer_fold")
    if candidate_event["mae"] >= base_event["mae"]:
        reasons.append("event_mae_not_improved")
    required_direction = max(
        minimum_event_direction_accuracy,
        base_event["actionable_direction_accuracy"],
    )
    if candidate_event["actionable_direction_accuracy"] < required_direction:
        reasons.append("event_direction_accuracy_not_improved")
    if extra_selected < max(1, math.ceil(fold_count / 2)):
        reasons.append("earnings_features_not_selected_consistently")

    return {
        "promotion_ready": not reasons,
        "automatic_promotion": False,
        "reasons": reasons,
        "comparison": {
            "validation_samples": candidate_samples,
            "overall_mae_delta": round(
                _metric(base, "mae") - _metric(candidate, "mae"), 6
            ),
            "return_correlation_delta": round(
                _metric(candidate, "return_correlation")
                - _metric(base, "return_correlation"),
                4,
            ),
            "event_samples": int(candidate_event["samples"]),
            "event_mae_delta": round(
                base_event["mae"] - candidate_event["mae"], 6
            ),
            "base_event_direction_accuracy": base_event[
                "actionable_direction_accuracy"
            ],
            "candidate_event_direction_accuracy": candidate_event[
                "actionable_direction_accuracy"
            ],
            "earnings_feature_selected_folds": extra_selected,
            "outer_folds": fold_count,
        },
    }


def _read(path: Path) -> dict[str, object]:
    """심볼릭 링크와 과대 보고서를 거부하고 JSON 객체를 읽는다."""

    resolved = path.resolve()
    if (
        not resolved.is_file()
        or resolved.is_symlink()
        or resolved.stat().st_size > 4 * 1024 * 1024
    ):
        raise ValueError("validation report is unavailable or unsafe")
    value = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("validation report must be an object")
    return value


def _save(path: Path, report: dict[str, object]) -> None:
    """판정 보고서를 후보 artifacts 경로에 원자적으로 저장한다."""

    target = path.resolve()
    if target.suffix.casefold() != ".json" or not target.is_relative_to(ARTIFACT_ROOT):
        raise ValueError("assessment output must be JSON inside artifacts")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    """드라이런 또는 실적 후보 판정을 수행하며 모델 파일은 변경하지 않는다."""

    args = parse_args()
    if args.dry_run:
        print(json.dumps({"assessment": "planned", "automatic_promotion": False}))
        return 0
    report = assess(
        _read(args.base),
        _read(args.candidate),
        minimum_event_samples=args.minimum_event_samples,
        minimum_event_direction_accuracy=args.minimum_event_direction_accuracy,
    )
    _save(args.output, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
