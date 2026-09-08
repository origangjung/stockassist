"""Run a non-promoting CUDA XGBoost walk-forward benchmark on local-AI data."""

import argparse
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
from sklearn.metrics import balanced_accuracy_score, brier_score_loss, roc_auc_score
from xgboost import XGBClassifier


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.ai.training.walk_forward_local_agents import (  # noqa: E402
    MODEL_FEATURES,
    dataset_feature_names,
    load_rows,
    timestamp_folds,
)


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument(
        "--agent",
        choices=sorted(MODEL_FEATURES),
        required=True,
    )
    parser.add_argument("--estimators", type=int, default=400)
    parser.add_argument("--max-depth", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=0.03)
    parser.add_argument("--min-child-weight", type=float, default=8.0)
    parser.add_argument("--reg-lambda", type=float, default=5.0)
    parser.add_argument("--splits", type=int, default=4)
    parser.add_argument("--purge-timestamps", type=int, default=5)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--extra-feature", action="append", default=[])
    parser.add_argument("--min-absolute-outcome", type=float, default=0.0)
    parser.add_argument("--outcome-column", default="future_excess_return")
    parser.add_argument("--require-positive-feature", action="append", default=[])
    parser.add_argument("--use-all-safe-features", action="store_true")
    return parser.parse_args()


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    if not 50 <= args.estimators <= 2000:
        raise ValueError("estimators must be between 50 and 2000")
    if not 1 <= args.max_depth <= 12:
        raise ValueError("max depth must be between 1 and 12")
    if not 0 < args.learning_rate <= 1:
        raise ValueError("learning rate must be between 0 and 1")
    if args.min_child_weight <= 0 or args.reg_lambda < 0:
        raise ValueError("regularization values are invalid")
    dataset_path = args.data_dir / f"{args.agent}.csv"
    base_features = (
        dataset_feature_names(dataset_path)
        if args.use_all_safe_features
        else MODEL_FEATURES[args.agent]
    )
    features = tuple(dict.fromkeys((*base_features, *args.extra_feature)))
    x, y, timestamps = load_rows(
        dataset_path,
        features,
        min_absolute_outcome=args.min_absolute_outcome,
        outcome_column=args.outcome_column,
        required_positive_features=tuple(args.require_positive_feature),
    )
    folds = timestamp_folds(
        timestamps,
        splits=args.splits,
        purge=args.purge_timestamps,
    )
    probabilities: list[float] = []
    actuals: list[int] = []
    fold_metrics: list[dict[str, float | int]] = []
    selected_device = ""
    for fold_number, (train, validation) in enumerate(folds, start=1):
        positives = int(y[train].sum())
        negatives = len(train) - positives
        model = XGBClassifier(
            n_estimators=args.estimators,
            max_depth=args.max_depth,
            learning_rate=args.learning_rate,
            min_child_weight=args.min_child_weight,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=args.reg_lambda,
            objective="binary:logistic",
            eval_metric="logloss",
            tree_method="hist",
            device="cuda",
            scale_pos_weight=negatives / max(positives, 1),
            random_state=42,
            n_jobs=4,
        )
        model.fit(x[train], y[train])
        config = json.loads(model.get_booster().save_config())
        selected_device = str(config["learner"]["generic_param"]["device"])
        if not selected_device.startswith("cuda"):
            raise RuntimeError("XGBoost did not select a CUDA device")
        model.set_params(device="cpu")
        model.get_booster().set_param({"device": "cpu"})
        fold_probabilities = model.predict_proba(x[validation])[:, 1]
        fold_actuals = y[validation]
        fold_metrics.append(
            {
                "fold": fold_number,
                "train": len(train),
                "validation": len(validation),
                "balanced_accuracy": round(
                    float(
                        balanced_accuracy_score(
                            fold_actuals,
                            fold_probabilities >= 0.5,
                        )
                    ),
                    4,
                ),
                "brier_score": round(
                    float(brier_score_loss(fold_actuals, fold_probabilities)), 4
                ),
            }
        )
        probabilities.extend(fold_probabilities.tolist())
        actuals.extend(fold_actuals.tolist())

    probability_array = np.asarray(probabilities)
    actual_array = np.asarray(actuals)
    report = {
        "gpu_benchmark": "ok",
        "agent": args.agent,
        "training_device": selected_device,
        "estimators_per_fold": args.estimators,
        "max_depth": args.max_depth,
        "learning_rate": args.learning_rate,
        "min_child_weight": args.min_child_weight,
        "reg_lambda": args.reg_lambda,
        "features": list(features),
        "minimum_absolute_outcome": args.min_absolute_outcome,
        "outcome_column": args.outcome_column,
        "required_positive_features": args.require_positive_feature,
        "rows": len(x),
        "validation_samples": len(actuals),
        "accuracy": round(
            float(np.mean((probability_array >= 0.5) == actual_array)), 4
        ),
        "balanced_accuracy": round(
            float(balanced_accuracy_score(actual_array, probability_array >= 0.5)), 4
        ),
        "brier_score": round(float(brier_score_loss(actual_array, probability_array)), 4),
        "roc_auc": round(float(roc_auc_score(actual_array, probability_array)), 4),
        "folds": fold_metrics,
        "artifact_promoted": False,
    }
    if args.output_dir is not None:
        output_dir = args.output_dir.resolve()
        artifact_root = (ROOT / "artifacts").resolve()
        if output_dir != artifact_root and artifact_root not in output_dir.parents:
            raise ValueError("output directory must stay inside artifacts")
        output_dir.mkdir(parents=True, exist_ok=True)
        positives = int(y.sum())
        negatives = len(y) - positives
        final_model = XGBClassifier(
            n_estimators=args.estimators,
            max_depth=args.max_depth,
            learning_rate=args.learning_rate,
            min_child_weight=args.min_child_weight,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=args.reg_lambda,
            objective="binary:logistic",
            eval_metric="logloss",
            tree_method="hist",
            device="cuda",
            scale_pos_weight=negatives / max(positives, 1),
            random_state=42,
            n_jobs=4,
        )
        final_model.fit(x, y)
        model_path = output_dir / f"{args.agent}-cuda-candidate.ubj"
        temporary_model = model_path.with_suffix(".tmp.ubj")
        final_model.save_model(temporary_model)
        temporary_model.replace(model_path)
        manifest = {
            "schema_version": 1,
            "agent": args.agent,
            "status": "candidate",
            "promoted": False,
            "trained_at": datetime.now(UTC).isoformat(),
            "training_rows": len(x),
            "training_device": selected_device,
            "model_sha256": sha256(model_path.read_bytes()).hexdigest(),
            "validation": report,
        }
        manifest_path = output_dir / f"{args.agent}-cuda-candidate.json"
        temporary_manifest = manifest_path.with_suffix(".tmp.json")
        temporary_manifest.write_text(
            json.dumps(manifest, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        temporary_manifest.replace(manifest_path)
        report["candidate_artifact"] = model_path.name
        report["candidate_manifest"] = manifest_path.name
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
