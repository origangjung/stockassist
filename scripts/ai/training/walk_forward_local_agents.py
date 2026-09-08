"""Evaluate local AI candidates with timestamp-grouped purged walk-forward folds."""

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, brier_score_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.features import (  # noqa: E402
    ETF_MODEL_FEATURES,
    ETF_SYNTHESIS_FEATURES,
    FEATURES,
    SYNTHESIS_FEATURES,
)
from app.local_ai.runtime import AGENTS  # noqa: E402


CORE_MODELS = (*AGENTS, "synthesis")
MODEL_FEATURES = {
    **FEATURES,
    "synthesis": SYNTHESIS_FEATURES,
    **ETF_MODEL_FEATURES,
    "etf_synthesis": ETF_SYNTHESIS_FEATURES,
}
NON_FEATURE_COLUMNS = frozenset(
    {
        "timestamp",
        "symbol",
        "label",
        "future_return",
        "close_price",
        "benchmark_future_return",
        "future_excess_return",
        "future_max_drawdown",
        "future_tone_change",
        "outcome_start_timestamp",
        "accession",
        "feature_timestamp",
        "valuation_filed",
        "valuation_price_timestamp",
        "earnings_fiscal_date",
        "earnings_reported_date",
        "earnings_available_date",
        "earnings_report_time",
        "reported_eps",
        "estimated_eps",
        "eps_surprise",
        "eps_surprise_percentage",
        "pit_per",
        "pit_pbr",
        "pit_psr",
        "pit_roe",
        "sector",
        "label_basis",
        "sector_neutral_future_return",
        "future_excess_return_cross_section_rank",
        "sample_weight",
        "horizon_days",
    }
)


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--agent", choices=["all", *MODEL_FEATURES], default="all")
    parser.add_argument("--splits", type=int, default=4)
    parser.add_argument("--purge-timestamps", type=int, default=5)
    parser.add_argument("--c-grid", default="0.002,0.01,0.05,0.1,0.5,1.0")
    parser.add_argument("--extra-feature", action="append", default=[])
    parser.add_argument("--min-absolute-outcome", type=float, default=0.0)
    parser.add_argument("--outcome-column", default="future_excess_return")
    parser.add_argument("--require-positive-feature", action="append", default=[])
    parser.add_argument("--positive-weight-grid", default="")
    parser.add_argument("--use-all-safe-features", action="store_true")
    return parser.parse_args()


def dataset_feature_names(path: Path) -> tuple[str, ...]:
    """`dataset_feature_names`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        fieldnames = csv.DictReader(source).fieldnames or []
    return tuple(name for name in fieldnames if name not in NON_FEATURE_COLUMNS)


def load_rows(
    path: Path,
    features: tuple[str, ...],
    *,
    min_absolute_outcome: float = 0.0,
    outcome_column: str = "future_excess_return",
    required_positive_features: tuple[str, ...] = (),
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """`load_rows`은(는) 필요한 데이터를 조회해 반환합니다."""

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    required = {"timestamp", "label", *features}
    if min_absolute_outcome:
        required.add(outcome_column)
    required.update(required_positive_features)
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"{path.name}: missing required columns")
    if min_absolute_outcome:
        rows = [
            row
            for row in rows
            if abs(float(row[outcome_column])) >= min_absolute_outcome
        ]
    if required_positive_features:
        rows = [
            row
            for row in rows
            if all(float(row[name]) > 0 for name in required_positive_features)
        ]
    timestamps = np.asarray([row["timestamp"] for row in rows])
    if timestamps.tolist() != sorted(timestamps.tolist()):
        raise ValueError(f"{path.name}: timestamps must be ordered")
    x = np.asarray([[float(row[name]) for name in features] for row in rows], dtype=float)
    y = np.asarray([int(row["label"]) for row in rows], dtype=np.int8)
    if not np.isfinite(x).all() or set(np.unique(y)) != {0, 1}:
        raise ValueError(f"{path.name}: invalid features or labels")
    return x, y, timestamps


def timestamp_folds(
    timestamps: np.ndarray, *, splits: int, purge: int
) -> list[tuple[np.ndarray, np.ndarray]]:
    """`timestamp_folds`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    unique = np.unique(timestamps)
    if splits < 2 or purge < 0 or len(unique) < 12:
        raise ValueError("insufficient timestamps or invalid split settings")
    initial = max(5, len(unique) // 3)
    validation_size = max(1, (len(unique) - initial - purge) // splits)
    folds: list[tuple[np.ndarray, np.ndarray]] = []
    validation_start = initial + purge
    while validation_start < len(unique) and len(folds) < splits:
        validation_end = min(len(unique), validation_start + validation_size)
        train_end = validation_start - purge
        train = np.flatnonzero(timestamps < unique[train_end])
        validation = np.flatnonzero(
            np.isin(timestamps, unique[validation_start:validation_end])
        )
        if len(train) >= 50 and len(validation) >= 10:
            folds.append((train, validation))
        validation_start = validation_end
    if len(folds) < 2:
        raise ValueError("could not construct enough walk-forward folds")
    return folds


def evaluate(
    x: np.ndarray,
    y: np.ndarray,
    folds: list[tuple[np.ndarray, np.ndarray]],
    *,
    inverse_regularization: float,
    balanced: bool,
    positive_weight: float | None = None,
) -> dict[str, float | int | bool]:
    """`evaluate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    probabilities: list[float] = []
    actuals: list[int] = []
    fold_balanced: list[float] = []
    selective_fold_balanced: dict[float, list[float]] = {
        cutoff: [] for cutoff in (0.55, 0.60, 0.65)
    }
    for train, validation in folds:
        if len(np.unique(y[train])) < 2 or len(np.unique(y[validation])) < 2:
            continue
        scaler = StandardScaler().fit(x[train])
        classifier = LogisticRegression(
            C=inverse_regularization,
            class_weight=(
                {0: 1.0, 1: positive_weight}
                if positive_weight is not None
                else "balanced"
                if balanced
                else None
            ),
            max_iter=3000,
            random_state=42,
        ).fit(scaler.transform(x[train]), y[train])
        fold_probabilities = classifier.predict_proba(scaler.transform(x[validation]))[:, 1]
        fold_actuals = y[validation]
        fold_balanced.append(
            balanced_accuracy_score(fold_actuals, fold_probabilities >= 0.5)
        )
        for cutoff, values in selective_fold_balanced.items():
            selected = (fold_probabilities >= cutoff - 1e-12) | (
                fold_probabilities <= 1 - cutoff + 1e-12
            )
            if selected.sum() >= 20 and len(np.unique(fold_actuals[selected])) == 2:
                values.append(
                    balanced_accuracy_score(
                        fold_actuals[selected],
                        fold_probabilities[selected] >= 0.5,
                    )
                )
        probabilities.extend(fold_probabilities.tolist())
        actuals.extend(fold_actuals.tolist())
    if len(fold_balanced) < 2:
        raise ValueError("not enough folds contain both classes")
    probability_array = np.asarray(probabilities)
    actual_array = np.asarray(actuals)
    positive_rate = float(np.mean(actual_array == 1))
    baseline_accuracy = max(positive_rate, 1.0 - positive_rate)
    accuracy = float(np.mean((probability_array >= 0.5) == actual_array))
    report = {
        "inverse_regularization": inverse_regularization,
        "class_weight_balanced": balanced,
        "positive_class_weight": positive_weight,
        "folds": len(fold_balanced),
        "validation_samples": len(actuals),
        "accuracy": round(accuracy, 4),
        "baseline_accuracy": round(baseline_accuracy, 4),
        "baseline_improvement": round(accuracy - baseline_accuracy, 4),
        "positive_rate": round(positive_rate, 4),
        "balanced_accuracy": round(
            float(balanced_accuracy_score(actual_array, probability_array >= 0.5)), 4
        ),
        "minimum_fold_balanced_accuracy": round(float(min(fold_balanced)), 4),
        "brier_score": round(float(brier_score_loss(actual_array, probability_array)), 4),
        "roc_auc": round(float(roc_auc_score(actual_array, probability_array)), 4),
    }
    selective_predictions = []
    for cutoff in (0.55, 0.60, 0.65):
        item = _selective_metrics(
            probability_array,
            actual_array,
            cutoff=cutoff,
        )
        fold_values = selective_fold_balanced[cutoff]
        if item is not None and fold_values:
            item["evaluated_folds"] = len(fold_values)
            item["minimum_fold_balanced_accuracy"] = round(
                float(min(fold_values)), 4
            )
            selective_predictions.append(item)
    report["selective_predictions"] = selective_predictions
    return report


def _selective_metrics(
    probabilities: np.ndarray,
    actuals: np.ndarray,
    *,
    cutoff: float,
) -> dict[str, float | int] | None:
    """`_selective_metrics`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    epsilon = 1e-12
    selected = (probabilities >= cutoff - epsilon) | (
        probabilities <= 1 - cutoff + epsilon
    )
    sample_count = int(selected.sum())
    if sample_count < 50:
        return None
    selected_probabilities = probabilities[selected]
    selected_actuals = actuals[selected]
    if len(np.unique(selected_actuals)) != 2:
        return None
    predictions = selected_probabilities >= 0.5
    return {
        "probability_cutoff": cutoff,
        "samples": sample_count,
        "coverage": round(sample_count / len(actuals), 4),
        "accuracy": round(float(np.mean(predictions == selected_actuals)), 4),
        "balanced_accuracy": round(
            float(balanced_accuracy_score(selected_actuals, predictions)), 4
        ),
        "brier_score": round(
            float(brier_score_loss(selected_actuals, selected_probabilities)), 4
        ),
        "roc_auc": round(
            float(roc_auc_score(selected_actuals, selected_probabilities)), 4
        ),
    }


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    c_grid = [float(value) for value in args.c_grid.split(",")]
    positive_weights = [
        float(value) for value in args.positive_weight_grid.split(",") if value
    ]
    if not c_grid or any(value <= 0 for value in c_grid):
        raise ValueError("C values must be positive")
    if not 0 <= args.min_absolute_outcome <= 1:
        raise ValueError("minimum absolute outcome must be between 0 and 1")
    if any(value <= 0 for value in positive_weights):
        raise ValueError("positive class weights must be positive")
    selected = (
        tuple(
            model
            for model in CORE_MODELS
            if (args.data_dir / f"{model}.csv").is_file()
        )
        if args.agent == "all"
        else (args.agent,)
    )
    if not selected:
        raise ValueError("data directory does not contain any supported datasets")
    if args.extra_feature and args.agent == "all":
        raise ValueError("extra features require one explicitly selected agent")
    report: dict[str, object] = {}
    for agent in selected:
        path = args.data_dir / f"{agent}.csv"
        base_features = (
            dataset_feature_names(path)
            if args.use_all_safe_features
            else MODEL_FEATURES[agent]
        )
        features = tuple(dict.fromkeys((*base_features, *args.extra_feature)))
        x, y, timestamps = load_rows(
            path,
            features,
            min_absolute_outcome=args.min_absolute_outcome,
            outcome_column=args.outcome_column,
            required_positive_features=tuple(args.require_positive_feature),
        )
        unique_timestamp_count = len(np.unique(timestamps))
        effective_purge = min(
            args.purge_timestamps,
            max(1, unique_timestamp_count // 20),
        )
        folds = timestamp_folds(
            timestamps,
            splits=args.splits,
            purge=effective_purge,
        )
        weight_settings = [(False, None), (True, None), *(
            (False, value) for value in positive_weights
        )]
        candidates = [
            evaluate(
                x,
                y,
                folds,
                inverse_regularization=value,
                balanced=balanced,
                positive_weight=positive_weight,
            )
            for value in c_grid
            for balanced, positive_weight in weight_settings
        ]
        candidates.sort(
            key=lambda item: (
                item["minimum_fold_balanced_accuracy"],
                item["balanced_accuracy"],
                -item["brier_score"],
            ),
            reverse=True,
        )
        report[agent] = {
            "rows": len(x),
            "timestamps": unique_timestamp_count,
            "purge_timestamps": effective_purge,
            "features": list(features),
            "minimum_absolute_outcome": args.min_absolute_outcome,
            "outcome_column": args.outcome_column,
            "required_positive_features": args.require_positive_feature,
            "best": candidates[0],
            "candidates_evaluated": len(candidates),
        }
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
