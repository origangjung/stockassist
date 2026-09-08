"""Train StockPilot specialist models from labeled CSV files.

Each CSV must be named after its agent and contain the feature columns declared
in app.local_ai.features.FEATURES plus a binary ``label`` column. Rows must be
ordered by time because the final 20 percent is reserved for validation.
"""

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.contracts import ModelName  # noqa: E402
from app.local_ai.features import (  # noqa: E402
    ETF_MODEL_FEATURES,
    ETF_SYNTHESIS_FEATURES,
    FEATURES,
    SYNTHESIS_FEATURES,
)
from app.local_ai.model import LocalLogisticModel  # noqa: E402
from app.local_ai.runtime import AGENTS  # noqa: E402


CORE_MODELS: tuple[ModelName, ...] = (*AGENTS, "synthesis")
MODELS: tuple[ModelName, ...] = (
    *CORE_MODELS,
    "etf_technical",
    "etf_risk",
    "etf_synthesis",
)
MAX_DATASET_BYTES = 512 * 1024 * 1024
MAX_DATASET_ROWS = 2_000_000


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description="Train directly owned local analysis models")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts" / "local-ai")
    parser.add_argument("--agent", choices=["all", *MODELS], default="all")
    parser.add_argument("--validation-gap", type=int, default=0)
    parser.add_argument("--iterations", type=int, default=1200)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=0.001)
    parser.add_argument("--trainer", choices=["custom", "sklearn"], default="custom")
    parser.add_argument("--inverse-regularization", type=float, default=0.1)
    parser.add_argument("--min-absolute-return", type=float, default=0.0)
    parser.add_argument("--outcome-column", default="future_return")
    parser.add_argument("--class-weight-balanced", action="store_true")
    parser.add_argument("--extra-feature", action="append", default=[])
    parser.add_argument("--positive-class-weight", type=float)
    parser.add_argument("--max-training-timestamps", type=int)
    parser.add_argument("--refit-full-data", action="store_true")
    parser.add_argument("--decision-threshold", type=float, default=0.5)
    parser.add_argument("--prediction-horizon-days", type=int, default=5)
    return parser.parse_args()


def load_dataset(
    path: Path,
    feature_names: tuple[str, ...],
    *,
    min_absolute_return: float = 0.0,
    outcome_column: str = "future_return",
    max_training_timestamps: int | None = None,
) -> tuple[np.ndarray, np.ndarray, int]:
    """`load_dataset`은(는) 필요한 데이터를 조회해 반환합니다."""

    if not path.is_file() or path.stat().st_size > MAX_DATASET_BYTES:
        raise ValueError(f"{path.name}: dataset is missing or exceeds the size limit")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if min_absolute_return:
        if not rows or outcome_column not in rows[0]:
            raise ValueError(f"{path.name}: {outcome_column} is required for return filtering")
        rows = [
            row
            for row in rows
            if abs(float(row[outcome_column])) >= min_absolute_return
        ]
    if len(rows) > MAX_DATASET_ROWS:
        raise ValueError(f"{path.name}: dataset exceeds the row limit")
    required = {*feature_names, "timestamp", "label"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0] if rows else []))
        raise ValueError(f"{path.name}: missing columns {missing}")
    try:
        timestamps = [_timestamp(row["timestamp"]) for row in rows]
        features = np.asarray(
            [[float(row[name]) for name in feature_names] for row in rows], dtype=float
        )
        labels = np.asarray([int(row["label"]) for row in rows], dtype=np.int8)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{path.name}: feature and label values must be numeric") from exc
    if timestamps != sorted(timestamps):
        raise ValueError(f"{path.name}: rows must be ordered by timestamp")
    if "symbol" in rows[0]:
        keys = [(row["timestamp"], row["symbol"].strip().upper()) for row in rows]
        if len(keys) != len(set(keys)):
            raise ValueError(f"{path.name}: duplicate timestamp and symbol rows")
    if max_training_timestamps is not None:
        if max_training_timestamps < 100:
            raise ValueError("max training timestamps must be at least 100")
        unique_timestamps = sorted(set(timestamps))
        if len(unique_timestamps) > max_training_timestamps:
            first_timestamp = unique_timestamps[-max_training_timestamps]
            first_index = timestamps.index(first_timestamp)
            rows = rows[first_index:]
            timestamps = timestamps[first_index:]
            features = features[first_index:]
            labels = labels[first_index:]
    desired = int(len(rows) * 0.8)
    validation_timestamp = timestamps[desired]
    validation_start = next(
        index for index, value in enumerate(timestamps) if value == validation_timestamp
    )
    if validation_start < 25 or validation_start >= len(rows):
        raise ValueError(f"{path.name}: timestamp-aligned validation split is too small")
    return features, labels, validation_start


def _timestamp(raw: str) -> datetime:
    """`_timestamp`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    value = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
    return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)


def train(
    agent: ModelName,
    data_dir: Path,
    output_dir: Path,
    validation_gap: int = 0,
    *,
    iterations: int = 1200,
    learning_rate: float = 0.05,
    l2: float = 0.001,
    trainer: str = "custom",
    inverse_regularization: float = 0.1,
    min_absolute_return: float = 0.0,
    outcome_column: str = "future_return",
    class_weight_balanced: bool = False,
    extra_features: tuple[str, ...] = (),
    positive_class_weight: float | None = None,
    max_training_timestamps: int | None = None,
    refit_full_data: bool = False,
    decision_threshold: float = 0.5,
    prediction_horizon_days: int = 5,
) -> dict:
    """`train`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다."""

    feature_names = (
        SYNTHESIS_FEATURES
        if agent == "synthesis"
        else ETF_SYNTHESIS_FEATURES
        if agent == "etf_synthesis"
        else ETF_MODEL_FEATURES.get(agent, FEATURES.get(agent))
    )
    if feature_names is None:
        raise ValueError(f"unsupported local model: {agent}")
    feature_names = tuple(dict.fromkeys((*feature_names, *extra_features)))
    features, labels, validation_start = load_dataset(
        data_dir / f"{agent}.csv",
        feature_names,
        min_absolute_return=min_absolute_return,
        outcome_column=outcome_column,
        max_training_timestamps=max_training_timestamps,
    )
    if trainer == "sklearn":
        model = LocalLogisticModel.train_sklearn(
            agent,
            feature_names,
            features,
            labels,
            validation_gap=validation_gap,
            inverse_regularization=inverse_regularization,
            validation_start=validation_start,
            class_weight_balanced=class_weight_balanced,
            positive_class_weight=positive_class_weight,
            refit_full_data=refit_full_data,
            decision_threshold=decision_threshold,
            prediction_horizon_days=prediction_horizon_days,
        )
    else:
        model = LocalLogisticModel.train(
            agent,
            feature_names,
            features,
            labels,
            validation_gap=validation_gap,
            validation_start=validation_start,
            iterations=iterations,
            learning_rate=learning_rate,
            l2=l2,
            decision_threshold=decision_threshold,
            prediction_horizon_days=prediction_horizon_days,
        )
    target = output_dir / f"{agent}.json"
    model.save(target)
    return {
        "agent": agent,
        "artifact": str(target),
        "model_version": model.artifact.model_version,
        "training_samples": model.artifact.training_samples,
        "metrics": model.artifact.metrics,
    }


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    if args.extra_feature and args.agent == "all":
        raise ValueError("extra features require one explicitly selected agent")
    selected = CORE_MODELS if args.agent == "all" else (args.agent,)
    results = [
        train(
            agent,
            args.data_dir,
            args.output_dir,
            args.validation_gap,
            iterations=args.iterations,
            learning_rate=args.learning_rate,
            l2=args.l2,
            trainer=args.trainer,
            inverse_regularization=args.inverse_regularization,
            min_absolute_return=args.min_absolute_return,
            outcome_column=args.outcome_column,
            class_weight_balanced=args.class_weight_balanced,
            extra_features=tuple(args.extra_feature),
            positive_class_weight=args.positive_class_weight,
            max_training_timestamps=args.max_training_timestamps,
            refit_full_data=args.refit_full_data,
            decision_threshold=args.decision_threshold,
            prediction_horizon_days=args.prediction_horizon_days,
        )
        for agent in selected
    ]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
