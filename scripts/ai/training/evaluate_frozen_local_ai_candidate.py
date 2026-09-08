"""Evaluate a frozen local AI challenger only on rows after its selection cutoff."""

from __future__ import annotations

import argparse
import csv
from datetime import date
import json
import os
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
DATASET_ROOT = (ROOT / "datasets").resolve()
ARTIFACT_ROOT = (ROOT / "artifacts").resolve()
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.model import (  # noqa: E402
    LocalLogisticModel,
    classification_metrics,
)
from app.local_ai.quality import assess_model_quality  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse frozen candidate evaluation paths and minimum evidence requirements."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--champion", type=Path, default=Path("artifacts/local-ai/risk.json"))
    parser.add_argument("--cutoff-date", type=date.fromisoformat, required=True)
    parser.add_argument("--minimum-rows", type=int, default=1_000)
    parser.add_argument("--minimum-timestamps", type=int, default=20)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def safe_path(path: Path, root: Path, *, suffix: str, must_exist: bool) -> Path:
    """Require an input or output to remain below its intended ignored-data root."""

    resolved = path.expanduser().resolve()
    if (
        resolved.suffix.casefold() != suffix
        or not resolved.is_relative_to(root)
        or resolved == root
        or resolved.is_symlink()
        or (must_exist and not resolved.is_file())
    ):
        raise ValueError(f"path must be a safe {suffix} file below {root.name}")
    return resolved


def load_forward_rows(
    path: Path,
    feature_names: tuple[str, ...],
    cutoff: date,
) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    """Load unique labeled rows strictly after the challenger selection date."""

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    required = {"timestamp", "symbol", "label", *feature_names}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("forward dataset is empty or missing required columns")
    selected = [row for row in rows if date.fromisoformat(row["timestamp"][:10]) > cutoff]
    keys = [(row["timestamp"], row["symbol"].strip().upper()) for row in selected]
    if len(keys) != len(set(keys)):
        raise ValueError("forward dataset contains duplicate timestamp and symbol rows")
    if not selected:
        return np.empty((0, len(feature_names))), np.empty(0), [], []
    try:
        features = np.asarray(
            [[float(row[name]) for name in feature_names] for row in selected],
            dtype=float,
        )
        labels = np.asarray([int(row["label"]) for row in selected], dtype=np.int8)
    except (TypeError, ValueError) as exc:
        raise ValueError("forward dataset contains invalid numeric values") from exc
    if not np.isfinite(features).all() or not set(np.unique(labels)).issubset({0, 1}):
        raise ValueError("forward dataset contains invalid features or labels")
    return features, labels, [row["timestamp"] for row in selected], [key[1] for key in keys]


def model_probabilities(model: LocalLogisticModel, features: np.ndarray) -> np.ndarray:
    """Run a frozen JSON model over rows in its signed feature order."""

    names = model.artifact.feature_names
    return np.asarray(
        [
            model.predict_probability(dict(zip(names, row, strict=True)))
            for row in features
        ],
        dtype=float,
    )


def evaluate(
    model: LocalLogisticModel,
    features: np.ndarray,
    labels: np.ndarray,
) -> dict[str, float]:
    """Evaluate a model using the decision threshold recorded in its signed artifact."""

    threshold = float(model.artifact.metrics.get("decision_threshold", 0.5))
    return classification_metrics(
        model_probabilities(model, features),
        labels,
        threshold=threshold,
    )


def build_report(
    candidate: LocalLogisticModel,
    champion: LocalLogisticModel,
    features: np.ndarray,
    labels: np.ndarray,
    timestamps: list[str],
    symbols: list[str],
    *,
    cutoff: date,
    minimum_rows: int,
    minimum_timestamps: int,
) -> dict[str, object]:
    """Build a no-promotion forward comparison or an awaiting-data report."""

    if minimum_rows < 200 or minimum_timestamps < 5:
        raise ValueError("forward evidence requirements are too small")
    timestamp_count = len(set(timestamps))
    enough_data = len(labels) >= minimum_rows and timestamp_count >= minimum_timestamps
    both_classes = set(np.unique(labels)) == {0, 1}
    report: dict[str, object] = {
        "schema_version": 1,
        "automatic_promotion": False,
        "cutoff_date": cutoff.isoformat(),
        "status": "evaluated" if enough_data and both_classes else "awaiting_data",
        "rows": len(labels),
        "timestamps": timestamp_count,
        "symbols": len(set(symbols)),
        "minimum_rows": minimum_rows,
        "minimum_timestamps": minimum_timestamps,
        "candidate_model_version": candidate.artifact.model_version,
        "champion_model_version": champion.artifact.model_version,
        "promotion_ready": False,
    }
    if not enough_data or not both_classes:
        report["reasons"] = [
            *([] if len(labels) >= minimum_rows else ["rows_below_minimum"]),
            *([] if timestamp_count >= minimum_timestamps else ["timestamps_below_minimum"]),
            *([] if both_classes else ["both_classes_required"]),
        ]
        return report

    candidate_metrics = evaluate(candidate, features, labels)
    champion_metrics = evaluate(champion, features, labels)
    assessment = assess_model_quality("risk", candidate_metrics)
    accuracy_delta = candidate_metrics["accuracy"] - champion_metrics["accuracy"]
    promotion_ready = assessment.accepted and accuracy_delta > 0.0
    report.update(
        period_start=min(timestamps),
        period_end=max(timestamps),
        candidate_metrics=candidate_metrics,
        champion_metrics=champion_metrics,
        accuracy_delta=round(accuracy_delta, 4),
        promotion_ready=promotion_ready,
        reasons=[
            *assessment.reasons,
            *([] if accuracy_delta > 0.0 else ["candidate_accuracy_not_above_champion"]),
        ],
    )
    return report


def save_report(path: Path, report: dict[str, object]) -> None:
    """Atomically persist forward evidence without changing either model."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> int:
    """Validate paths, compare frozen models, and never activate a candidate."""

    args = parse_args()
    data_path = safe_path(
        args.data,
        DATASET_ROOT,
        suffix=".csv",
        must_exist=not args.dry_run,
    )
    candidate_path = safe_path(args.candidate, ARTIFACT_ROOT, suffix=".json", must_exist=True)
    champion_path = safe_path(args.champion, ARTIFACT_ROOT, suffix=".json", must_exist=True)
    output_path = safe_path(args.output, ARTIFACT_ROOT, suffix=".json", must_exist=False)
    if args.dry_run:
        print("forward_validation=planned automatic_promotion=false")
        return 0
    candidate = LocalLogisticModel.load(candidate_path, expected_agent="risk")
    champion = LocalLogisticModel.load(champion_path, expected_agent="risk")
    if candidate.artifact.feature_names != champion.artifact.feature_names:
        raise ValueError("candidate and champion feature schemas differ")
    features, labels, timestamps, symbols = load_forward_rows(
        data_path,
        tuple(candidate.artifact.feature_names),
        args.cutoff_date,
    )
    report = build_report(
        candidate,
        champion,
        features,
        labels,
        timestamps,
        symbols,
        cutoff=args.cutoff_date,
        minimum_rows=args.minimum_rows,
        minimum_timestamps=args.minimum_timestamps,
    )
    save_report(output_path, report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
