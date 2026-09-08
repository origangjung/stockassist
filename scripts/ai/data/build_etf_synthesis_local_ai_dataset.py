"""Build leakage-aware ETF synthesis data from walk-forward predictions."""

import argparse
import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.features import (  # noqa: E402
    ETF_MODEL_FEATURES,
    ETF_SYNTHESIS_FEATURES,
)
from app.local_ai.macro_features import MACRO_FEATURES  # noqa: E402
from app.local_ai.model import LocalLogisticModel  # noqa: E402


EMBARGO_DAYS = 10


@dataclass(frozen=True)
class WalkForwardModel:
    """데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다."""

    predictor: LocalLogisticModel
    validation_accuracy: float


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(
        description="Build walk-forward ETF synthesis training data"
    )
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--folds", type=int, default=10)
    parser.add_argument("--initial-fraction", type=float, default=0.5)
    parser.add_argument("--min-absolute-return", type=float, default=0.02)
    return parser.parse_args()


def _read(path: Path) -> list[dict]:
    """`_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    for row in rows:
        row["_date"] = date.fromisoformat(row["timestamp"][:10])
    rows.sort(key=lambda row: (row["_date"], row["symbol"]))
    return rows


def _train(model_name: str, rows: list[dict], cutoff: date):
    """`_train`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다."""

    names = ETF_MODEL_FEATURES[model_name]
    eligible = [
        row for row in rows if row["_date"] < cutoff - timedelta(days=EMBARGO_DAYS)
    ]
    if model_name == "etf_technical":
        eligible = [
            row for row in eligible if abs(float(row["future_return"])) >= 0.02
        ]
    labels = np.asarray([int(row["label"]) for row in eligible], dtype=np.int8)
    if len(eligible) < 50 or len(np.unique(labels)) != 2:
        return None
    features = np.asarray(
        [[float(row[name]) for name in names] for row in eligible], dtype=float
    )
    evaluator = LocalLogisticModel.train_sklearn(
        model_name,
        names,
        features,
        labels,
        class_weight_balanced=model_name == "etf_technical",
    )
    predictor = LocalLogisticModel.train_sklearn(
        model_name,
        names,
        features,
        labels,
        validation_start=len(features) - 1,
        class_weight_balanced=model_name == "etf_technical",
    )
    return WalkForwardModel(
        predictor=predictor,
        validation_accuracy=evaluator.artifact.metrics.get("accuracy", 0.0),
    )


def _summary(model: WalkForwardModel, row: dict, model_name: str) -> tuple[float, float]:
    """`_summary`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    names = ETF_MODEL_FEATURES[model_name]
    probability = model.predictor.predict_probability(
        {name: float(row[name]) for name in names}
    )
    confidence = min(
        1.0,
        abs(probability - 0.5)
        * 2
        * max(model.validation_accuracy, 0.5),
    )
    return probability, confidence


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    if not 0.25 <= args.initial_fraction <= 0.8 or args.folds < 2:
        raise ValueError("initial_fraction or folds is outside the supported range")

    technical_rows = _read(args.data_dir / "etf_technical.csv")
    risk_rows = _read(args.data_dir / "etf_risk.csv")
    risk_by_key = {
        (row["timestamp"], row["symbol"]): row for row in risk_rows
    }
    base_rows = [
        row
        for row in technical_rows
        if abs(float(row["future_return"])) >= args.min_absolute_return
    ]
    unique_dates = sorted({row["_date"] for row in base_rows})
    first = int(len(unique_dates) * args.initial_fraction)
    evaluation_dates = unique_dates[first:]
    fold_size = max(1, (len(evaluation_dates) + args.folds - 1) // args.folds)
    output_rows: list[dict] = []

    for offset in range(0, len(evaluation_dates), fold_size):
        fold_dates = set(evaluation_dates[offset : offset + fold_size])
        cutoff = min(fold_dates)
        technical_model = _train("etf_technical", technical_rows, cutoff)
        risk_model = _train("etf_risk", risk_rows, cutoff)
        if technical_model is None or risk_model is None:
            continue
        for base in base_rows:
            if base["_date"] not in fold_dates:
                continue
            risk = risk_by_key.get((base["timestamp"], base["symbol"]))
            if risk is None:
                continue
            technical_probability, technical_confidence = _summary(
                technical_model, base, "etf_technical"
            )
            risk_probability, risk_confidence = _summary(
                risk_model, risk, "etf_risk"
            )
            output_rows.append(
                {
                    "timestamp": base["timestamp"],
                    "symbol": base["symbol"],
                    "technical_probability": technical_probability,
                    "technical_confidence": technical_confidence,
                    "risk_probability": risk_probability,
                    "risk_confidence": risk_confidence,
                    **{name: base[name] for name in MACRO_FEATURES},
                    "label": base["label"],
                }
            )

    if len(output_rows) < 50:
        raise ValueError("not enough walk-forward ETF synthesis rows were generated")
    target = args.output_dir / "etf_synthesis.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=["timestamp", "symbol", *ETF_SYNTHESIS_FEATURES, "label"],
        )
        writer.writeheader()
        writer.writerows(output_rows)
    print(
        f"etf_synthesis={len(output_rows)} "
        f"dates={output_rows[0]['timestamp'][:10]}..{output_rows[-1]['timestamp'][:10]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
