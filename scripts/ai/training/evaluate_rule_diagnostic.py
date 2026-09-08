"""Evaluate the rule-based diagnostic on out-of-fold specialist predictions."""

import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.contracts import AgentName  # noqa: E402
from app.local_ai.diagnostic import (  # noqa: E402
    RULE_SYNTHESIS_VERSION,
    calculate_diagnostic,
    directional_signal,
)


DEFAULT_SPECIALISTS: tuple[AgentName, ...] = ("investor_flow", "risk")
SCHEMA_VERSION = 1


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--folds", type=int, default=4)
    parser.add_argument(
        "--specialist", action="append", choices=DEFAULT_SPECIALISTS
    )
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    """`read_rows`은(는) 필요한 데이터를 조회해 반환합니다."""

    if not path.is_file() or path.is_symlink() or path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("diagnostic dataset is missing or invalid")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows or not {"timestamp", "symbol", "label"}.issubset(rows[0]):
        raise ValueError("diagnostic dataset has an invalid schema")
    rows.sort(key=lambda row: (row["timestamp"], row["symbol"]))
    return rows


def evaluate(
    rows: list[dict[str, str]],
    specialists: tuple[AgentName, ...],
    *,
    folds: int,
) -> dict[str, object]:
    """`evaluate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if len(specialists) < 2 or len(set(specialists)) != len(specialists):
        raise ValueError("at least two unique specialists are required")
    if folds < 2:
        raise ValueError("at least two folds are required")
    evaluated = []
    for row in rows:
        results = {}
        for agent in specialists:
            available = float(row[f"{agent}_available"]) == 1.0
            probability = float(row[f"{agent}_probability"])
            confidence = float(row[f"{agent}_confidence"])
            results[agent] = {
                "status": "available" if available else "data_unavailable",
                "probability": probability,
                "confidence": confidence,
                "signal": directional_signal(agent, probability) if available else None,
            }
        calculation = calculate_diagnostic(results, specialists)
        if calculation is None or calculation.signal == "neutral":
            continue
        evaluated.append(
            {
                "timestamp": row["timestamp"],
                "actual": int(row["label"]),
                "predicted": int(calculation.signal == "positive"),
            }
        )
    if len(evaluated) < 50:
        raise ValueError("fewer than 50 directional diagnostic rows are available")
    unique_timestamps = sorted({row["timestamp"] for row in evaluated})
    fold_size = max(1, (len(unique_timestamps) + folds - 1) // folds)
    fold_metrics = []
    for offset in range(0, len(unique_timestamps), fold_size):
        selected_dates = set(unique_timestamps[offset : offset + fold_size])
        selected = [row for row in evaluated if row["timestamp"] in selected_dates]
        if selected:
            fold_metrics.append(_classification_metrics(selected))
    metrics = _classification_metrics(evaluated)
    metrics.update(
        {
            "source_rows": len(rows),
            "directional_rows": len(evaluated),
            "coverage": round(len(evaluated) / len(rows), 4),
            "folds": len(fold_metrics),
            "minimum_fold_balanced_accuracy": round(
                min(float(item["balanced_accuracy"]) for item in fold_metrics), 4
            ),
        }
    )
    approved = (
        len(evaluated) >= 1_000
        and float(metrics["coverage"]) >= 0.05
        and float(metrics["balanced_accuracy"]) > 0.52
        and float(metrics["minimum_fold_balanced_accuracy"]) > 0.50
        and float(metrics["baseline_improvement"]) > 0.0
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "version": RULE_SYNTHESIS_VERSION,
        "approved": approved,
        "specialists": list(specialists),
        "metrics": metrics,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }


def _classification_metrics(rows: list[dict[str, int | str]]) -> dict[str, float]:
    """`_classification_metrics`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    actual = [int(row["actual"]) for row in rows]
    predicted = [int(row["predicted"]) for row in rows]
    positive_rate = sum(actual) / len(actual)
    accuracy = sum(a == p for a, p in zip(actual, predicted, strict=True)) / len(actual)
    true_positive = sum(a == 1 and p == 1 for a, p in zip(actual, predicted, strict=True))
    true_negative = sum(a == 0 and p == 0 for a, p in zip(actual, predicted, strict=True))
    positives = sum(actual)
    negatives = len(actual) - positives
    balanced = (
        (true_positive / positives if positives else 0.0)
        + (true_negative / negatives if negatives else 0.0)
    ) / 2
    baseline = max(positive_rate, 1.0 - positive_rate)
    return {
        "accuracy": round(accuracy, 4),
        "balanced_accuracy": round(balanced, 4),
        "positive_rate": round(positive_rate, 4),
        "baseline_accuracy": round(baseline, 4),
        "baseline_improvement": round(accuracy - baseline, 4),
    }


def save_policy(path: Path, policy: dict[str, object]) -> None:
    """`save_policy`은(는) 데이터를 저장하거나 기존 상태에 추가합니다."""

    payload = dict(policy)
    unsigned = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    payload["content_sha256"] = sha256(unsigned.encode()).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    specialists = tuple(args.specialist or DEFAULT_SPECIALISTS)
    report = evaluate(read_rows(args.dataset), specialists, folds=args.folds)
    if args.output:
        save_policy(args.output, report)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
