"""하이퍼파라미터 선택과 최종 평가 시점을 분리한 중첩 시간 검증을 실행한다."""

import argparse
from collections import Counter
import csv
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, brier_score_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = (ROOT / "artifacts").resolve()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.contracts import ModelName  # noqa: E402
from app.local_ai.quality import assess_model_quality  # noqa: E402
from scripts.ai.training.walk_forward_local_agents import (  # noqa: E402
    MODEL_FEATURES,
    NON_FEATURE_COLUMNS,
    dataset_feature_names,
    load_rows,
    timestamp_folds,
)


@dataclass(frozen=True)
class CandidateSetting:
    """`CandidateSetting` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    inverse_regularization: float
    class_weight_balanced: bool

    @property
    def key(self) -> str:
        """`key`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        weight = "balanced" if self.class_weight_balanced else "unweighted"
        return f"c={self.inverse_regularization:g},{weight}"


@dataclass(frozen=True)
class SelectedCandidate:
    """내부 시간 검증에서 선택된 규제 설정과 피처 열 묶음이다."""

    setting: CandidateSetting
    feature_set: str
    columns: tuple[int, ...]
    decision_threshold: float


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--agent", choices=sorted(MODEL_FEATURES), required=True)
    parser.add_argument("--outer-splits", type=int, default=5)
    parser.add_argument("--inner-splits", type=int, default=3)
    parser.add_argument("--purge-timestamps", type=int, default=5)
    parser.add_argument("--c-grid", default="0.002,0.01,0.05,0.1,0.5,1.0")
    parser.add_argument(
        "--class-weight-mode",
        choices=("both", "balanced", "unweighted"),
        default="both",
        help="내부 시간 검증에서 비교할 클래스 가중치 모드",
    )
    parser.add_argument("--sample-weight-column")
    parser.add_argument("--max-training-timestamps", type=int)
    parser.add_argument("--fixed-decision-threshold", type=float)
    parser.add_argument("--min-absolute-outcome", type=float, default=0.0)
    parser.add_argument("--outcome-column", default="future_excess_return")
    parser.add_argument("--prediction-horizon-days", type=int, default=5)
    parser.add_argument("--extra-feature", action="append", default=[])
    parser.add_argument("--use-all-safe-features", action="store_true")
    parser.add_argument(
        "--candidate-extra-feature-set",
        action="append",
        default=[],
        help="내부 fold에서만 선택할 쉼표 구분 추가 피처 묶음. 기본 피처도 항상 후보에 포함된다.",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def candidate_settings(
    c_values: list[float],
    class_weight_mode: str = "both",
) -> tuple[CandidateSetting, ...]:
    """규제 강도마다 일반 가중치와 균형 가중치 후보를 만든다."""

    if not c_values or any(value <= 0 for value in c_values):
        raise ValueError("C values must be positive")
    if class_weight_mode not in {"both", "balanced", "unweighted"}:
        raise ValueError("class weight mode must be both, balanced, or unweighted")
    weight_modes = {
        "both": (False, True),
        "balanced": (True,),
        "unweighted": (False,),
    }[class_weight_mode]
    return tuple(
        CandidateSetting(value, balanced)
        for value in c_values
        for balanced in weight_modes
    )


def resolve_features(
    data_path: Path,
    agent: str,
    extra_features: list[str],
    *,
    use_all_safe_features: bool = False,
) -> tuple[str, ...]:
    """운영 기본 피처에 CSV에 존재하는 안전한 후보 피처만 추가한다."""

    available = set(dataset_feature_names(data_path))
    requested = tuple(dict.fromkeys(value.strip() for value in extra_features if value.strip()))
    invalid = [
        name
        for name in requested
        if name in NON_FEATURE_COLUMNS or name not in available
    ]
    if invalid:
        raise ValueError(f"invalid extra features: {','.join(invalid)}")
    base = dataset_feature_names(data_path) if use_all_safe_features else MODEL_FEATURES[agent]
    return (*base, *[name for name in requested if name not in base])


def resolve_feature_sets(
    data_path: Path,
    agent: str,
    fixed_extra_features: list[str],
    candidate_extra_feature_sets: list[str],
    *,
    use_all_safe_features: bool = False,
) -> tuple[tuple[str, ...], dict[str, tuple[int, ...]]]:
    """후보 피처 묶음을 검증하고 전체 행렬에서 사용할 열 인덱스로 변환한다."""
    base = resolve_features(
        data_path,
        agent,
        fixed_extra_features,
        use_all_safe_features=use_all_safe_features,
    )
    candidates: list[tuple[str, tuple[str, ...]]] = [("base", base)]
    for raw_group in candidate_extra_feature_sets:
        extras = [value.strip() for value in raw_group.split(",") if value.strip()]
        resolved = resolve_features(
            data_path,
            agent,
            [*fixed_extra_features, *extras],
            use_all_safe_features=use_all_safe_features,
        )
        key = "extra:" + ",".join(extras)
        if not extras or any(existing_key == key for existing_key, _ in candidates):
            raise ValueError("candidate feature sets must be non-empty and unique")
        candidates.append((key, resolved))
    all_features = tuple(dict.fromkeys(name for _, names in candidates for name in names))
    indexes = {name: index for index, name in enumerate(all_features)}
    return all_features, {
        key: tuple(indexes[name] for name in names)
        for key, names in candidates
    }


def load_sample_weights(path: Path, column: str) -> np.ndarray:
    """CSV의 양수·유한 표본 가중치를 원본 행 순서대로 읽는다."""

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows or column not in rows[0]:
        raise ValueError("sample weight column is missing")
    try:
        weights = np.asarray([float(row[column]) for row in rows], dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("sample weights must be numeric") from exc
    if not np.isfinite(weights).all() or (weights <= 0).any():
        raise ValueError("sample weights must be finite and positive")
    return weights


def _calibration_error(
    actual: np.ndarray,
    probability: np.ndarray,
    sample_weights: np.ndarray,
) -> float:
    """`_calibration_error`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    boundaries = np.linspace(0.0, 1.0, 11)
    error = 0.0
    for index in range(10):
        upper_inclusive = index == 9
        selected = (probability >= boundaries[index]) & (
            probability <= boundaries[index + 1]
            if upper_inclusive
            else probability < boundaries[index + 1]
        )
        if selected.any():
            selected_weights = sample_weights[selected]
            error += float(selected_weights.sum() / sample_weights.sum()) * abs(
                float(np.average(probability[selected], weights=selected_weights))
                - float(np.average(actual[selected], weights=selected_weights))
            )
    return error


def _metrics(
    actual: np.ndarray,
    probability: np.ndarray,
    sample_weights: np.ndarray | None = None,
    *,
    threshold: float = 0.5,
    predictions: np.ndarray | None = None,
) -> dict[str, float | int]:
    """`_metrics`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    weights = (
        np.ones(len(actual), dtype=float)
        if sample_weights is None
        else np.asarray(sample_weights, dtype=float)
    )
    resolved_predictions = (
        probability >= threshold
        if predictions is None
        else np.asarray(predictions, dtype=bool)
    )
    if len(resolved_predictions) != len(actual):
        raise ValueError("predictions must align with actual labels")
    positive_rate = float(np.average(actual, weights=weights))
    baseline = max(positive_rate, 1.0 - positive_rate)
    accuracy = float(np.average(resolved_predictions == actual, weights=weights))
    return {
        "validation_samples": len(actual),
        "validation_weight": round(float(weights.sum()), 4),
        "accuracy": round(accuracy, 4),
        "baseline_accuracy": round(baseline, 4),
        "baseline_improvement": round(accuracy - baseline, 4),
        "balanced_accuracy": round(
            float(
                balanced_accuracy_score(
                    actual,
                    resolved_predictions,
                    sample_weight=weights,
                )
            ),
            4,
        ),
        "brier_score": round(
            float(brier_score_loss(actual, probability, sample_weight=weights)), 4
        ),
        "calibration_error": round(
            _calibration_error(actual, probability, weights), 4
        ),
        "roc_auc": round(
            float(roc_auc_score(actual, probability, sample_weight=weights)), 4
        ),
        "positive_rate": round(positive_rate, 4),
        "decision_threshold": round(float(threshold), 4),
    }


def _correct_balanced_probabilities(
    probability: np.ndarray,
    labels: np.ndarray,
    sample_weights: np.ndarray | None = None,
) -> np.ndarray:
    """균형 클래스 가중치로 왜곡된 사후확률을 실제 학습 발생률로 되돌린다."""

    weights = (
        np.ones(len(labels), dtype=float)
        if sample_weights is None
        else np.asarray(sample_weights, dtype=float)
    )
    prior = float(np.average(labels, weights=weights))
    if not 0.0 < prior < 1.0:
        raise ValueError("probability correction requires both classes")
    clipped = np.clip(probability, 1e-8, 1.0 - 1e-8)
    odds = clipped / (1.0 - clipped)
    corrected_odds = odds * prior / (1.0 - prior)
    return corrected_odds / (1.0 + corrected_odds)


def _select_threshold(
    actual: np.ndarray,
    probability: np.ndarray,
    sample_weights: np.ndarray | None = None,
) -> float:
    """내부 검증 결과에서 균형 정확도가 가장 안정적인 판정 임계값을 고른다."""

    candidates = np.unique(
        np.concatenate(
            (
                np.asarray([0.5]),
                np.quantile(probability, np.linspace(0.05, 0.95, 91)),
            )
        )
    )
    feasible: list[tuple[tuple[float, float, float], float]] = []
    fallback: list[tuple[tuple[float, float, float], float]] = []
    for threshold in candidates:
        metrics = _metrics(
            actual,
            probability,
            sample_weights,
            threshold=float(threshold),
        )
        score = (
            float(metrics["balanced_accuracy"]),
            float(metrics["baseline_improvement"]),
            -abs(float(threshold) - 0.5),
        )
        fallback.append((score, float(threshold)))
        if (
            float(metrics["baseline_improvement"]) > 0.0
            and float(metrics["balanced_accuracy"]) > 0.5
        ):
            feasible.append(
                (
                    (
                        min(
                            float(metrics["balanced_accuracy"]) - 0.5,
                            float(metrics["baseline_improvement"]),
                        ),
                        float(metrics["balanced_accuracy"]),
                        -abs(float(threshold) - 0.5),
                    ),
                    float(threshold),
                )
            )
    pool = feasible if feasible else fallback
    return max(pool, key=lambda item: item[0])[1]


def _select_setting(
    x: np.ndarray,
    y: np.ndarray,
    timestamps: np.ndarray,
    settings: tuple[CandidateSetting, ...],
    *,
    inner_splits: int,
    purge: int,
    sample_weights: np.ndarray | None = None,
    feature_sets: dict[str, tuple[int, ...]] | None = None,
    max_training_timestamps: int | None = None,
    fixed_decision_threshold: float | None = None,
) -> SelectedCandidate:
    """`_select_setting`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    effective_purge = min(purge, max(1, len(np.unique(timestamps)) // 20))
    folds = timestamp_folds(timestamps, splits=inner_splits, purge=effective_purge)
    resolved_sets = feature_sets or {"all": tuple(range(x.shape[1]))}
    scored: list[tuple[tuple[float, float, float], SelectedCandidate]] = []
    for feature_set, columns in resolved_sets.items():
      for setting in settings:
        probabilities: list[float] = []
        actuals: list[int] = []
        weights: list[float] = []
        fold_outputs: list[tuple[np.ndarray, np.ndarray, np.ndarray | None]] = []
        for train, validation in folds:
            train = _limit_training_window(
                train,
                timestamps,
                max_training_timestamps,
            )
            train_weights = sample_weights[train] if sample_weights is not None else None
            validation_weights = (
                sample_weights[validation] if sample_weights is not None else None
            )
            selected_x = x[:, columns]
            scaler = StandardScaler().fit(selected_x[train], sample_weight=train_weights)
            classifier = LogisticRegression(
                C=setting.inverse_regularization,
                class_weight="balanced" if setting.class_weight_balanced else None,
                max_iter=3000,
                random_state=42,
            ).fit(
                scaler.transform(selected_x[train]),
                y[train],
                sample_weight=train_weights,
            )
            fold_probability = classifier.predict_proba(
                scaler.transform(selected_x[validation])
            )[:, 1]
            if setting.class_weight_balanced:
                fold_probability = _correct_balanced_probabilities(
                    fold_probability,
                    y[train],
                    train_weights,
                )
            fold_outputs.append((y[validation], fold_probability, validation_weights))
            probabilities.extend(fold_probability.tolist())
            actuals.extend(y[validation].tolist())
            weights.extend(
                validation_weights.tolist()
                if validation_weights is not None
                else [1.0] * len(validation)
            )
        actual_array = np.asarray(actuals)
        probability_array = np.asarray(probabilities)
        weight_array = np.asarray(weights)
        threshold = (
            fixed_decision_threshold
            if fixed_decision_threshold is not None
            else _select_threshold(actual_array, probability_array, weight_array)
        )
        report = _metrics(
            actual_array,
            probability_array,
            weight_array,
            threshold=threshold,
        )
        fold_reports = [
            _metrics(
                fold_actual,
                fold_probability,
                fold_weights,
                threshold=threshold,
            )
            for fold_actual, fold_probability, fold_weights in fold_outputs
        ]
        fold_balanced = [float(item["balanced_accuracy"]) for item in fold_reports]
        fold_improvements = [
            float(item["baseline_improvement"]) for item in fold_reports
        ]
        scored.append(
            (
                (
                    min(fold_improvements),
                    min(fold_balanced),
                    float(report["balanced_accuracy"]),
                ),
                SelectedCandidate(setting, feature_set, columns, threshold),
            )
        )
    return max(scored, key=lambda item: item[0])[1]


def nested_validate(
    agent: ModelName,
    x: np.ndarray,
    y: np.ndarray,
    timestamps: np.ndarray,
    settings: tuple[CandidateSetting, ...],
    *,
    outer_splits: int,
    inner_splits: int,
    purge: int,
    sample_weights: np.ndarray | None = None,
    feature_sets: dict[str, tuple[int, ...]] | None = None,
    max_training_timestamps: int | None = None,
    fixed_decision_threshold: float | None = None,
) -> dict[str, object]:
    """각 바깥 학습 구간 안에서만 설정을 선택하고 다음 시점에서 평가한다."""

    effective_purge = min(purge, max(1, len(np.unique(timestamps)) // 20))
    outer_folds = timestamp_folds(
        timestamps,
        splits=outer_splits,
        purge=effective_purge,
    )
    if fixed_decision_threshold is not None and not 0.0 < fixed_decision_threshold < 1.0:
        raise ValueError("fixed decision threshold must be between zero and one")
    probabilities: list[float] = []
    actuals: list[int] = []
    outer_weights: list[float] = []
    outer_predictions: list[bool] = []
    fold_reports: list[dict[str, object]] = []
    selected_settings: list[str] = []
    selected_feature_sets: list[str] = []
    for fold_number, (train, validation) in enumerate(outer_folds, start=1):
        train = _limit_training_window(train, timestamps, max_training_timestamps)
        candidate = _select_setting(
            x[train],
            y[train],
            timestamps[train],
            settings,
            inner_splits=inner_splits,
            purge=effective_purge,
            sample_weights=sample_weights[train] if sample_weights is not None else None,
            feature_sets=feature_sets,
            max_training_timestamps=max_training_timestamps,
            fixed_decision_threshold=fixed_decision_threshold,
        )
        setting = candidate.setting
        train_weights = sample_weights[train] if sample_weights is not None else None
        validation_weights = (
            sample_weights[validation] if sample_weights is not None else None
        )
        selected_x = x[:, candidate.columns]
        scaler = StandardScaler().fit(selected_x[train], sample_weight=train_weights)
        classifier = LogisticRegression(
            C=setting.inverse_regularization,
            class_weight="balanced" if setting.class_weight_balanced else None,
            max_iter=3000,
            random_state=42,
        ).fit(
            scaler.transform(selected_x[train]),
            y[train],
            sample_weight=train_weights,
        )
        fold_probability = classifier.predict_proba(scaler.transform(selected_x[validation]))[:, 1]
        if setting.class_weight_balanced:
            fold_probability = _correct_balanced_probabilities(
                fold_probability,
                y[train],
                train_weights,
            )
        fold_actual = y[validation]
        if len(np.unique(fold_actual)) < 2:
            raise ValueError("outer validation fold must contain both classes")
        fold_metrics = _metrics(
            fold_actual,
            fold_probability,
            validation_weights,
            threshold=candidate.decision_threshold,
        )
        fold_reports.append(
            {
                "fold": fold_number,
                "selected_setting": setting.key,
                "selected_feature_set": candidate.feature_set,
                "selected_threshold": round(candidate.decision_threshold, 4),
                "train_rows": len(train),
                **fold_metrics,
            }
        )
        selected_settings.append(setting.key)
        selected_feature_sets.append(candidate.feature_set)
        probabilities.extend(fold_probability.tolist())
        actuals.extend(fold_actual.tolist())
        outer_predictions.extend(
            (fold_probability >= candidate.decision_threshold).tolist()
        )
        if sample_weights is not None:
            outer_weights.extend(validation_weights.tolist())

    aggregate = _metrics(
        np.asarray(actuals),
        np.asarray(probabilities),
        np.asarray(outer_weights) if sample_weights is not None else None,
        predictions=np.asarray(outer_predictions),
    )
    aggregate["decision_threshold"] = round(
        float(np.median([item["selected_threshold"] for item in fold_reports])),
        4,
    )
    minimum_fold_balanced = min(
        float(item["balanced_accuracy"]) for item in fold_reports
    )
    minimum_fold_improvement = min(
        float(item["baseline_improvement"]) for item in fold_reports
    )
    fold_positive_rates = [float(item["positive_rate"]) for item in fold_reports]
    positive_rate_range = max(fold_positive_rates) - min(fold_positive_rates)
    aggregate["minimum_fold_balanced_accuracy"] = round(minimum_fold_balanced, 4)
    aggregate["minimum_fold_baseline_improvement"] = round(
        minimum_fold_improvement, 4
    )
    aggregate["fold_positive_rate_range"] = round(positive_rate_range, 4)
    assessment = assess_model_quality(agent, aggregate)
    promotion_reasons = list(assessment.reasons)
    if minimum_fold_balanced <= 0.5:
        promotion_reasons.append("minimum_fold_balanced_accuracy<=0.50")
    selection_counts = Counter(selected_settings)
    feature_selection_counts = Counter(selected_feature_sets)
    if max(selection_counts.values()) / len(selected_settings) < 0.6:
        promotion_reasons.append("hyperparameter_selection_unstable")
    if max(feature_selection_counts.values()) / len(selected_feature_sets) < 0.6:
        promotion_reasons.append("feature_selection_unstable")
    if positive_rate_range > 0.25:
        promotion_reasons.append("fold_positive_rate_range>0.25")
    if minimum_fold_improvement <= 0:
        promotion_reasons.append("minimum_fold_baseline_improvement<=0")
    return {
        "metrics": aggregate,
        "folds": fold_reports,
        "selected_settings": dict(sorted(selection_counts.items())),
        "selected_feature_sets": dict(sorted(feature_selection_counts.items())),
        "promotion_ready": not promotion_reasons,
        "promotion_reasons": promotion_reasons,
    }


def _limit_training_window(
    train: np.ndarray,
    timestamps: np.ndarray,
    maximum_timestamps: int | None,
) -> np.ndarray:
    """학습 인덱스를 예측 시점 직전의 제한된 거래일 창으로 줄인다."""

    if maximum_timestamps is None:
        return train
    if maximum_timestamps < 100:
        raise ValueError("max training timestamps must be at least 100")
    unique = np.unique(timestamps[train])
    if len(unique) <= maximum_timestamps:
        return train
    cutoff = unique[-maximum_timestamps]
    return train[timestamps[train] >= cutoff]


def safe_output_path(value: Path) -> Path:
    """검증 보고서가 Git 제외 artifact 디렉터리 밖에 기록되지 않게 제한한다."""

    path = value.expanduser().resolve()
    if path.suffix.casefold() != ".json" or not path.is_relative_to(ARTIFACT_ROOT):
        raise ValueError("nested validation output must be JSON inside artifacts")
    return path


def save_report(path: Path, report: dict[str, object]) -> None:
    """중첩 검증 보고서를 배타적 임시 파일에 기록한 뒤 원자 교체한다."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor: int | None = None
    try:
        descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = None
            json.dump(report, stream, ensure_ascii=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    data_path = (args.data_dir / f"{args.agent}.csv").resolve()
    features, feature_sets = resolve_feature_sets(
        data_path,
        args.agent,
        args.extra_feature,
        args.candidate_extra_feature_set,
        use_all_safe_features=args.use_all_safe_features,
    )
    if not 0.0 <= args.min_absolute_outcome <= 1.0:
        raise ValueError("minimum absolute outcome must be between zero and one")
    if args.sample_weight_column and args.min_absolute_outcome:
        raise ValueError("sample weights cannot be combined with outcome filtering")
    with data_path.open("r", encoding="utf-8-sig", newline="") as source:
        total_rows = sum(1 for _ in csv.DictReader(source))
    x, y, timestamps = load_rows(
        data_path,
        features,
        min_absolute_outcome=args.min_absolute_outcome,
        outcome_column=args.outcome_column,
    )
    sample_weights = (
        load_sample_weights(data_path, args.sample_weight_column)
        if args.sample_weight_column
        else None
    )
    if sample_weights is not None and len(sample_weights) != len(x):
        raise ValueError("sample weights do not align with dataset rows")
    settings = candidate_settings(
        [float(value) for value in args.c_grid.split(",")],
        args.class_weight_mode,
    )
    result = nested_validate(
        args.agent,
        x,
        y,
        timestamps,
        settings,
        outer_splits=args.outer_splits,
        inner_splits=args.inner_splits,
        purge=args.purge_timestamps,
        sample_weights=sample_weights,
        feature_sets=feature_sets,
        max_training_timestamps=args.max_training_timestamps,
        fixed_decision_threshold=args.fixed_decision_threshold,
    )
    row_coverage = len(x) / max(total_rows, 1)
    if args.min_absolute_outcome and row_coverage < 0.5:
        result["promotion_ready"] = False
        reasons = list(result.get("promotion_reasons", []))
        reasons.append("filtered_row_coverage<0.50")
        result["promotion_reasons"] = reasons
    report = {
        "agent": args.agent,
        "dataset_sha256": sha256(data_path.read_bytes()).hexdigest(),
        "rows": len(x),
        "source_rows": total_rows,
        "row_coverage": round(row_coverage, 4),
        "timestamps": len(np.unique(timestamps)),
        "features": list(features),
        "candidate_feature_sets": {
            key: [features[index] for index in columns]
            for key, columns in feature_sets.items()
        },
        "outer_splits": args.outer_splits,
        "inner_splits": args.inner_splits,
        "purge_timestamps": args.purge_timestamps,
        "sample_weight_column": args.sample_weight_column,
        "class_weight_mode": args.class_weight_mode,
        "max_training_timestamps": args.max_training_timestamps,
        "fixed_decision_threshold": args.fixed_decision_threshold,
        "minimum_absolute_outcome": args.min_absolute_outcome,
        "outcome_column": args.outcome_column,
        "prediction_horizon_days": args.prediction_horizon_days,
        **result,
    }
    if args.output:
        save_report(safe_output_path(args.output), report)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
