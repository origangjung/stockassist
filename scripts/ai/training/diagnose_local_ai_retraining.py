"""Diagnose why broader local-AI datasets fail to improve out-of-time quality."""

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.features import FEATURES  # noqa: E402
from app.local_ai.runtime import AGENTS  # noqa: E402


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--reference-data-dir", type=Path)
    parser.add_argument("--agent", choices=("all", *AGENTS), default="all")
    return parser.parse_args()


def safe_auc(actual: np.ndarray, score: np.ndarray) -> float | None:
    """`safe_auc`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if len(np.unique(actual)) != 2:
        return None
    return float(roc_auc_score(actual, score))


def load_rows(path: Path) -> list[dict[str, str]]:
    """`load_rows`은(는) 필요한 데이터를 조회해 반환합니다."""

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def compare_reference(
    rows: list[dict[str, str]], reference_path: Path
) -> dict[str, float | int]:
    """`compare_reference`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    reference = {
        (row["timestamp"], row.get("symbol", "")): row
        for row in load_rows(reference_path)
    }
    candidate = {(row["timestamp"], row.get("symbol", "")): row for row in rows}
    overlap = reference.keys() & candidate.keys()
    agreement = sum(reference[key]["label"] == candidate[key]["label"] for key in overlap)
    return {
        "reference_rows": len(reference),
        "candidate_rows": len(candidate),
        "overlap_rows": len(overlap),
        "overlap_label_agreement": round(agreement / max(len(overlap), 1), 4),
        "candidate_row_retention": round(len(candidate) / max(len(reference), 1), 4),
    }


def analyze(
    path: Path, agent: str, reference_path: Path | None = None
) -> dict[str, object]:
    """`analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다."""

    rows = load_rows(path)
    features = FEATURES[agent]
    timestamps = np.asarray([row["timestamp"] for row in rows])
    labels = np.asarray([int(row["label"]) for row in rows], dtype=np.int8)
    values = np.asarray(
        [[float(row[feature]) for feature in features] for row in rows],
        dtype=float,
    )
    desired = int(len(rows) * 0.8)
    validation_timestamp = timestamps[desired]
    validation_start = int(np.flatnonzero(timestamps == validation_timestamp)[0])
    train_x, validation_x = values[:validation_start], values[validation_start:]
    train_y, validation_y = labels[:validation_start], labels[validation_start:]

    scaler = StandardScaler().fit(train_x)
    classifier = LogisticRegression(
        C=0.1,
        class_weight="balanced",
        max_iter=3000,
        random_state=42,
    ).fit(scaler.transform(train_x), train_y)
    train_probability = classifier.predict_proba(scaler.transform(train_x))[:, 1]
    validation_probability = classifier.predict_proba(
        scaler.transform(validation_x)
    )[:, 1]

    standardized_shift = np.abs(
        (validation_x.mean(axis=0) - train_x.mean(axis=0))
        / np.where(train_x.std(axis=0) > 1e-12, train_x.std(axis=0), 1.0)
    )
    shift_order = np.argsort(standardized_shift)[::-1][:3]

    excess_returns = None
    if "future_excess_return" in rows[0]:
        excess_returns = np.asarray(
            [float(row["future_excess_return"]) for row in rows], dtype=float
        )

    report: dict[str, object] = {
        "agent": agent,
        "rows": len(rows),
        "symbols": len({row.get("symbol", "") for row in rows}),
        "unique_timestamps": len(np.unique(timestamps)),
        "rows_per_timestamp": round(len(rows) / len(np.unique(timestamps)), 2),
        "date_start": str(timestamps[0]),
        "date_end": str(timestamps[-1]),
        "validation_start": str(validation_timestamp),
        "train_positive_rate": round(float(train_y.mean()), 4),
        "validation_positive_rate": round(float(validation_y.mean()), 4),
        "positive_rate_shift": round(float(validation_y.mean() - train_y.mean()), 4),
        "majority_baseline": round(
            float(max(validation_y.mean(), 1 - validation_y.mean())), 4
        ),
        "train_auc": round(safe_auc(train_y, train_probability) or 0.5, 4),
        "validation_auc": round(
            safe_auc(validation_y, validation_probability) or 0.5, 4
        ),
        "generalization_gap": round(
            (safe_auc(train_y, train_probability) or 0.5)
            - (safe_auc(validation_y, validation_probability) or 0.5),
            4,
        ),
        "validation_balanced_accuracy": round(
            float(
                balanced_accuracy_score(
                    validation_y, validation_probability >= 0.5
                )
            ),
            4,
        ),
        "largest_feature_shifts": [
            {
                "feature": features[index],
                "standard_deviations": round(float(standardized_shift[index]), 3),
            }
            for index in shift_order
        ],
    }
    if excess_returns is not None:
        validation_excess = excess_returns[validation_start:]
        report.update(
            {
                "label_matches_positive_excess_return": round(
                    float(np.mean(labels == (excess_returns > 0))), 4
                ),
                "validation_near_zero_excess_return_rate": round(
                    float(np.mean(np.abs(validation_excess) < 0.01)), 4
                ),
                "validation_median_absolute_excess_return": round(
                    float(np.median(np.abs(validation_excess))), 6
                ),
            }
        )
    if reference_path is not None and reference_path.is_file():
        report["reference_comparison"] = compare_reference(rows, reference_path)
    return report


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    agents = AGENTS if args.agent == "all" else (args.agent,)
    reports = [
        analyze(
            args.data_dir / f"{agent}.csv",
            agent,
            args.reference_data_dir / f"{agent}.csv"
            if args.reference_data_dir
            else None,
        )
        for agent in agents
    ]
    print(json.dumps(reports, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
