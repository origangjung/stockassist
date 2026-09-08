"""기술 AI의 미래 초과수익 회귀 후보를 중첩 시간순 검증한다.

기존 이진 분류와 달리 작은 가격 변동은 중립으로 취급한다. 외부 검증 구간의
정보가 하이퍼파라미터 선택에 섞이지 않도록 각 외부 학습 구간 안에서만 Ridge
규제 강도를 선택하며, 이 스크립트는 운영 모델을 자동 교체하지 않는다.
"""

import argparse
from collections import Counter
import csv
import json
import os
from pathlib import Path
import sys

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import balanced_accuracy_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = (ROOT / "artifacts").resolve()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.features import FEATURES  # noqa: E402
from scripts.ai.training.nested_walk_forward_local_agent import (  # noqa: E402
    resolve_feature_sets,
)
from scripts.ai.training.walk_forward_local_agents import timestamp_folds  # noqa: E402
from scripts.ai.training.walk_forward_local_agents import (  # noqa: E402
    NON_FEATURE_COLUMNS,
    dataset_feature_names,
)


def parse_args() -> argparse.Namespace:
    """명령줄 인자를 검증 가능한 기본값과 함께 읽는다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument(
        "--model-name",
        default="technical_expected_excess_return_ridge",
        help="후보 보고서를 구분할 모델 이름",
    )
    parser.add_argument("--outer-splits", type=int, default=5)
    parser.add_argument("--inner-splits", type=int, default=3)
    parser.add_argument("--purge-timestamps", type=int, default=10)
    parser.add_argument("--alpha-grid", default="0.1,1,10,100")
    parser.add_argument(
        "--candidate-extra-feature-set",
        action="append",
        default=[],
        help="내부 시간 검증에서만 기본 피처와 비교할 쉼표 구분 피처 묶음",
    )
    parser.add_argument(
        "--base-feature",
        action="append",
        default=[],
        help="기본 기술 피처 대신 사용할 명시적 안전 피처(반복 가능)",
    )
    parser.add_argument(
        "--blas-threads",
        type=int,
        choices=range(1, 5),
        default=1,
        help="선형대수 연산 스레드 수(PC 부하 억제를 위해 기본 1)",
    )
    parser.add_argument(
        "--neutral-return",
        type=float,
        default=0.01,
        help="상승·하락으로 판정하지 않을 초과수익 절댓값(기본 1%%)",
    )
    parser.add_argument(
        "--evaluation-subgroup-feature",
        help="학습에는 넣지 않고 별도 성능을 계산할 0/1 피처",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_regression_rows(
    path: Path,
    features: tuple[str, ...] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """기술 피처와 미래 초과수익을 시간순 CSV에서 안전하게 읽는다."""

    features = features or FEATURES["technical"]
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    required = {"timestamp", "future_excess_return", *features}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"{path.name}: missing required columns")
    timestamps = np.asarray([row["timestamp"] for row in rows])
    if timestamps.tolist() != sorted(timestamps.tolist()):
        raise ValueError(f"{path.name}: timestamps must be ordered")
    x = np.asarray([[float(row[name]) for name in features] for row in rows])
    y = np.asarray([float(row["future_excess_return"]) for row in rows])
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError(f"{path.name}: features and outcomes must be finite")
    return x, y, timestamps


def return_states(values: np.ndarray, neutral_return: float) -> np.ndarray:
    """수익률을 하락(-1), 중립(0), 상승(1)의 세 상태로 변환한다."""

    if neutral_return <= 0:
        raise ValueError("neutral return must be positive")
    return np.where(values > neutral_return, 1, np.where(values < -neutral_return, -1, 0))


def resolve_requested_feature_sets(
    path: Path,
    base_features: list[str],
    candidate_extra_feature_sets: list[str],
) -> tuple[tuple[str, ...], dict[str, tuple[int, ...]]]:
    """명시한 기본 피처와 추가 묶음이 CSV의 안전한 열인지 검증한다."""

    if not base_features:
        return resolve_feature_sets(
            path, "technical", [], candidate_extra_feature_sets
        )
    available = set(dataset_feature_names(path))
    base = tuple(dict.fromkeys(name.strip() for name in base_features if name.strip()))
    if not base:
        raise ValueError("base features must not be empty")
    requested_sets: list[tuple[str, tuple[str, ...]]] = [("base", base)]
    for raw_group in candidate_extra_feature_sets:
        extras = tuple(
            dict.fromkeys(name.strip() for name in raw_group.split(",") if name.strip())
        )
        if not extras:
            raise ValueError("candidate feature sets must be non-empty")
        requested_sets.append(("extra:" + ",".join(extras), (*base, *extras)))
    requested = {name for _, names in requested_sets for name in names}
    invalid = sorted(
        name for name in requested if name in NON_FEATURE_COLUMNS or name not in available
    )
    if invalid:
        raise ValueError(f"invalid features: {','.join(invalid)}")
    all_features = tuple(dict.fromkeys(name for _, names in requested_sets for name in names))
    indexes = {name: index for index, name in enumerate(all_features)}
    return all_features, {
        key: tuple(indexes[name] for name in names)
        for key, names in requested_sets
    }


def _fit_predict(
    train_x: np.ndarray,
    train_y: np.ndarray,
    validation_x: np.ndarray,
    alpha: float,
) -> np.ndarray:
    """학습 구간으로만 표준화한 Ridge 모델의 검증 예측을 반환한다."""

    scaler = StandardScaler().fit(train_x)
    model = Ridge(alpha=alpha).fit(scaler.transform(train_x), train_y)
    return model.predict(scaler.transform(validation_x))


def _select_candidate(
    x: np.ndarray,
    y: np.ndarray,
    timestamps: np.ndarray,
    train: np.ndarray,
    alphas: tuple[float, ...],
    feature_sets: dict[str, tuple[int, ...]],
    *,
    inner_splits: int,
    purge: int,
) -> tuple[float, str, tuple[int, ...]]:
    """외부 학습 구간 내부에서 규제 강도와 피처 묶음을 함께 선택한다."""

    inner_folds = timestamp_folds(
        timestamps[train], splits=inner_splits, purge=purge
    )
    scores: dict[tuple[float, str], list[float]] = {
        (alpha, name): [] for alpha in alphas for name in feature_sets
    }
    for inner_train, inner_validation in inner_folds:
        for alpha in alphas:
            for name, columns in feature_sets.items():
                predicted = _fit_predict(
                    x[train][inner_train][:, columns],
                    y[train][inner_train],
                    x[train][inner_validation][:, columns],
                    alpha,
                )
                scores[(alpha, name)].append(
                    float(mean_absolute_error(y[train][inner_validation], predicted))
                )
    alpha, name = min(
        scores,
        key=lambda candidate: (
            float(np.mean(scores[candidate])),
            len(feature_sets[candidate[1]]),
            candidate[0],
            candidate[1],
        ),
    )
    return alpha, name, feature_sets[name]


def nested_validate(
    x: np.ndarray,
    y: np.ndarray,
    timestamps: np.ndarray,
    alphas: tuple[float, ...],
    *,
    outer_splits: int = 5,
    inner_splits: int = 3,
    purge: int = 10,
    neutral_return: float = 0.01,
    feature_sets: dict[str, tuple[int, ...]] | None = None,
    model_name: str = "technical_expected_excess_return_ridge",
    subgroup_values: np.ndarray | None = None,
    subgroup_name: str | None = None,
) -> dict[str, object]:
    """과거만 보는 중첩 검증으로 회귀와 3상태 판정 품질을 계산한다."""

    if not alphas or any(alpha <= 0 for alpha in alphas):
        raise ValueError("alphas must be positive")
    feature_sets = feature_sets or {"base": tuple(range(x.shape[1]))}
    if not feature_sets or any(not columns for columns in feature_sets.values()):
        raise ValueError("feature sets must contain at least one column")
    if any(max(columns) >= x.shape[1] or min(columns) < 0 for columns in feature_sets.values()):
        raise ValueError("feature set column is outside the feature matrix")
    if subgroup_values is not None and len(subgroup_values) != len(y):
        raise ValueError("subgroup values must align with outcomes")
    actual: list[float] = []
    predicted: list[float] = []
    selected: Counter[str] = Counter()
    selected_features: Counter[str] = Counter()
    subgroup_actual: list[float] = []
    subgroup_predicted: list[float] = []
    folds_report: list[dict[str, object]] = []
    for fold_number, (train, validation) in enumerate(
        timestamp_folds(timestamps, splits=outer_splits, purge=purge), start=1
    ):
        alpha, feature_set, columns = _select_candidate(
            x,
            y,
            timestamps,
            train,
            alphas,
            feature_sets,
            inner_splits=inner_splits,
            purge=purge,
        )
        fold_prediction = _fit_predict(
            x[train][:, columns], y[train], x[validation][:, columns], alpha
        )
        actual.extend(y[validation].tolist())
        predicted.extend(fold_prediction.tolist())
        if subgroup_values is not None:
            subgroup_selected = subgroup_values[validation] >= 0.5
            subgroup_actual.extend(y[validation][subgroup_selected].tolist())
            subgroup_predicted.extend(fold_prediction[subgroup_selected].tolist())
        selected[f"alpha={alpha:g}"] += 1
        selected_features[feature_set] += 1
        fold_mae = float(mean_absolute_error(y[validation], fold_prediction))
        fold_baseline_mae = float(
            mean_absolute_error(y[validation], np.zeros_like(y[validation]))
        )
        folds_report.append(
            {
                "fold": fold_number,
                "training_samples": len(train),
                "validation_samples": len(validation),
                "validation_start": str(timestamps[validation[0]]),
                "validation_end": str(timestamps[validation[-1]]),
                "selected_alpha": alpha,
                "selected_feature_set": feature_set,
                "mae": round(fold_mae, 6),
                "zero_baseline_mae": round(fold_baseline_mae, 6),
                "mae_improvement": round(fold_baseline_mae - fold_mae, 6),
            }
        )

    actual_array = np.asarray(actual)
    predicted_array = np.asarray(predicted)
    actual_state = return_states(actual_array, neutral_return)
    predicted_state = return_states(predicted_array, neutral_return)
    active = predicted_state != 0
    state_accuracy = float(np.mean(actual_state == predicted_state))
    state_baseline = float(np.max(np.bincount(actual_state + 1)) / len(actual_state))
    correlation = (
        float(np.corrcoef(actual_array, predicted_array)[0, 1])
        if np.std(predicted_array) > 0 and np.std(actual_array) > 0
        else 0.0
    )
    metrics: dict[str, float | int] = {
        "unique_timestamps": len(np.unique(timestamps)),
        "validation_samples": len(actual_array),
        "mae": round(float(mean_absolute_error(actual_array, predicted_array)), 6),
        "zero_baseline_mae": round(float(mean_absolute_error(actual_array, np.zeros_like(actual_array))), 6),
        "mae_improvement": round(
            float(mean_absolute_error(actual_array, np.zeros_like(actual_array)))
            - float(mean_absolute_error(actual_array, predicted_array)),
            6,
        ),
        "return_correlation": round(correlation, 4),
        "three_state_accuracy": round(state_accuracy, 4),
        "three_state_baseline_accuracy": round(state_baseline, 4),
        "three_state_balanced_accuracy": round(
            float(balanced_accuracy_score(actual_state, predicted_state)), 4
        ),
        "actionable_coverage": round(float(np.mean(active)), 4),
        "actionable_direction_accuracy": round(
            float(np.mean(np.sign(predicted_array[active]) == np.sign(actual_array[active])))
            if active.any()
            else 0.0,
            4,
        ),
        "minimum_fold_mae_improvement": min(
            float(fold["mae_improvement"]) for fold in folds_report
        ),
    }
    if subgroup_values is not None:
        subgroup_actual_array = np.asarray(subgroup_actual)
        subgroup_predicted_array = np.asarray(subgroup_predicted)
        subgroup_active = np.abs(subgroup_predicted_array) > neutral_return
        subgroup_metrics: dict[str, float | int] = {
            "samples": len(subgroup_actual_array),
            "mae": round(
                float(mean_absolute_error(subgroup_actual_array, subgroup_predicted_array))
                if len(subgroup_actual_array)
                else 0.0,
                6,
            ),
            "zero_baseline_mae": round(
                float(np.mean(np.abs(subgroup_actual_array)))
                if len(subgroup_actual_array)
                else 0.0,
                6,
            ),
            "actionable_coverage": round(
                float(np.mean(subgroup_active)) if len(subgroup_active) else 0.0,
                4,
            ),
            "actionable_direction_accuracy": round(
                float(
                    np.mean(
                        np.sign(subgroup_predicted_array[subgroup_active])
                        == np.sign(subgroup_actual_array[subgroup_active])
                    )
                )
                if subgroup_active.any()
                else 0.0,
                4,
            ),
        }
        metrics[f"subgroup:{subgroup_name or 'selected'}"] = subgroup_metrics
    return {
        "model": model_name,
        "target": "future_excess_return",
        "neutral_return": neutral_return,
        "promotion_ready": bool(
            metrics["mae_improvement"] > 0
            and metrics["return_correlation"] > 0
            and metrics["three_state_balanced_accuracy"] > 1 / 3
            and metrics["minimum_fold_mae_improvement"] >= 0
            and metrics["unique_timestamps"] >= 500
        ),
        "metrics": metrics,
        "selected_settings": dict(sorted(selected.items())),
        "selected_feature_sets": dict(sorted(selected_features.items())),
        "folds": folds_report,
    }


def safe_output_path(path: Path) -> Path:
    """후보 보고서가 운영 모델 밖의 artifacts 폴더에만 기록되게 제한한다."""

    resolved = path.resolve()
    if resolved != ARTIFACT_ROOT and ARTIFACT_ROOT not in resolved.parents:
        raise ValueError("output must be inside artifacts")
    return resolved


def save_report(path: Path, report: dict[str, object]) -> None:
    """부분 파일이 남지 않도록 임시 파일을 원자적으로 교체한다."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def main() -> int:
    """데이터를 읽고 후보 검증 보고서를 저장한 뒤 요약을 출력한다."""

    args = parse_args()
    alphas = tuple(float(value) for value in args.alpha_grid.split(","))
    features, feature_sets = resolve_requested_feature_sets(
        args.data,
        args.base_feature,
        args.candidate_extra_feature_set,
    )
    subgroup_index: int | None = None
    if args.evaluation_subgroup_feature:
        available = set(dataset_feature_names(args.data))
        if args.evaluation_subgroup_feature not in available:
            raise ValueError("evaluation subgroup feature is unavailable or unsafe")
        if args.evaluation_subgroup_feature not in features:
            features = (*features, args.evaluation_subgroup_feature)
        subgroup_index = features.index(args.evaluation_subgroup_feature)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "validation": "planned",
                    "data": str(args.data),
                    "features": len(features),
                    "feature_sets": list(feature_sets),
                    "output": str(args.output),
                    "automatic_promotion": False,
                },
                ensure_ascii=False,
            )
        )
        return 0
    x, y, timestamps = load_regression_rows(args.data, features)
    # 대규모 CSV 검증 중에도 PC의 다른 작업을 방해하지 않도록 BLAS 병렬도를 제한한다.
    with threadpool_limits(limits=args.blas_threads):
        report = nested_validate(
            x,
            y,
            timestamps,
            alphas,
            outer_splits=args.outer_splits,
            inner_splits=args.inner_splits,
            purge=args.purge_timestamps,
            neutral_return=args.neutral_return,
            feature_sets=feature_sets,
            model_name=args.model_name,
            subgroup_values=x[:, subgroup_index] if subgroup_index is not None else None,
            subgroup_name=args.evaluation_subgroup_feature,
        )
    output = safe_output_path(args.output)
    save_report(output, report)
    print(json.dumps({"output": str(output), **report["metrics"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
