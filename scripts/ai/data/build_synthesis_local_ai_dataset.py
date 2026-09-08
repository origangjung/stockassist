"""Build leakage-aware synthesis data from walk-forward specialist predictions."""

import argparse
from bisect import bisect_right
import csv
from datetime import date, timedelta
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.features import FEATURES, SYNTHESIS_FEATURES  # noqa: E402
from app.local_ai.model import LocalLogisticModel  # noqa: E402
from app.local_ai.runtime import AGENTS  # noqa: E402


EMBARGO_DAYS = {
    "technical": 10,
    "financial": 180,
    "news": 7,
    "investor_flow": 10,
    "risk": 10,
}
MAX_FEATURE_AGE_DAYS = {
    "technical": 0,
    "financial": 500,
    "news": 3,
    "investor_flow": 7,
    "risk": 0,
}


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description="Build walk-forward synthesis data")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--folds", type=int, default=8)
    parser.add_argument("--initial-fraction", type=float, default=0.5)
    parser.add_argument("--min-absolute-return", type=float, default=0.0)
    parser.add_argument("--trainer", choices=["custom", "sklearn"], default="sklearn")
    return parser.parse_args()


def _read(path: Path) -> list[dict]:
    """`_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    for row in rows:
        row["_date"] = date.fromisoformat(row["timestamp"][:10])
    rows.sort(key=lambda row: (row["_date"], row["symbol"]))
    return rows


def _train_specialist(agent: str, rows: list[dict], cutoff: date, trainer: str):
    """`_train_specialist`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다."""

    eligible = [
        row
        for row in rows
        if row["_date"] < cutoff - timedelta(days=EMBARGO_DAYS[agent])
    ]
    if len(eligible) < 50:
        return None
    labels = np.asarray([int(row["label"]) for row in eligible], dtype=np.int8)
    if len(np.unique(labels)) != 2:
        return None
    features = np.asarray(
        [[float(row[name]) for name in FEATURES[agent]] for row in eligible],
        dtype=float,
    )
    if trainer == "sklearn":
        return LocalLogisticModel.train_sklearn(
            agent, FEATURES[agent], features, labels
        )
    return LocalLogisticModel.train(agent, FEATURES[agent], features, labels)


def _indexes(rows_by_agent: dict[str, list[dict]]):
    """`_indexes`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    result = {}
    for agent, rows in rows_by_agent.items():
        by_symbol: dict[str, list[dict]] = {}
        for row in rows:
            by_symbol.setdefault(row["symbol"], []).append(row)
        result[agent] = {
            symbol: ([row["_date"] for row in values], values)
            for symbol, values in by_symbol.items()
        }
    return result


def _latest_row(index, symbol: str, target_date: date, max_age_days: int):
    """`_latest_row`은(는) 필요한 데이터를 조회해 반환합니다."""

    values = index.get(symbol)
    if values is None:
        return None
    dates, rows = values
    position = bisect_right(dates, target_date) - 1
    if position < 0 or (target_date - dates[position]).days > max_age_days:
        return None
    return rows[position]


def _specialist_values(agent: str, model, row: dict | None) -> tuple[float, float, float]:
    """`_specialist_values`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if model is None or row is None:
        return 0.5, 0.0, 0.0
    values = {name: float(row[name]) for name in FEATURES[agent]}
    probability = model.predict_probability(values)
    accuracy = model.artifact.metrics.get("accuracy", 0.0)
    confidence = min(1.0, abs(probability - 0.5) * 2 * max(accuracy, 0.5))
    return probability, confidence, 1.0


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    if not 0.25 <= args.initial_fraction <= 0.8 or args.folds < 2:
        raise ValueError("initial_fraction or folds is outside the supported range")
    rows_by_agent = {
        agent: _read(args.data_dir / f"{agent}.csv") for agent in AGENTS
    }
    base_rows = rows_by_agent["technical"]
    if args.min_absolute_return:
        base_rows = [
            row
            for row in base_rows
            if abs(float(row["future_return"])) >= args.min_absolute_return
        ]
    unique_dates = sorted({row["_date"] for row in base_rows})
    first = int(len(unique_dates) * args.initial_fraction)
    evaluation_dates = unique_dates[first:]
    fold_size = max(1, (len(evaluation_dates) + args.folds - 1) // args.folds)
    indexes = _indexes(rows_by_agent)
    output_rows = []
    for offset in range(0, len(evaluation_dates), fold_size):
        fold_dates = evaluation_dates[offset : offset + fold_size]
        cutoff = fold_dates[0]
        models = {
            agent: _train_specialist(agent, rows_by_agent[agent], cutoff, args.trainer)
            for agent in AGENTS
        }
        for base in base_rows:
            target_date = base["_date"]
            if target_date not in fold_dates:
                continue
            values = {"timestamp": base["timestamp"], "symbol": base["symbol"]}
            for agent in AGENTS:
                feature_row = _latest_row(
                    indexes[agent],
                    base["symbol"],
                    target_date,
                    MAX_FEATURE_AGE_DAYS[agent],
                )
                probability, confidence, available = _specialist_values(
                    agent, models[agent], feature_row
                )
                values[f"{agent}_probability"] = probability
                values[f"{agent}_confidence"] = confidence
                values[f"{agent}_available"] = available
            values["label"] = base["label"]
            output_rows.append(values)
    target = args.output_dir / "synthesis.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=["timestamp", "symbol", *SYNTHESIS_FEATURES, "label"],
        )
        writer.writeheader()
        writer.writerows(output_rows)
    coverage = {
        agent: sum(float(row[f"{agent}_available"]) for row in output_rows)
        for agent in AGENTS
    }
    print(f"synthesis={len(output_rows)} coverage={coverage}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
