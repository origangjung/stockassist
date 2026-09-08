"""Compare chronological holdout quality for additive local-AI feature groups."""

import argparse
import csv
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--group", action="append", default=[])
    parser.add_argument("--inverse-regularization", type=float, default=0.1)
    parser.add_argument("--min-absolute-return", type=float, default=0.0)
    return parser.parse_args()


def _names(value: str) -> list[str]:
    """`_names`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return [name.strip() for name in value.split(",") if name.strip()]


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    with args.input.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if args.min_absolute_return:
        rows = [
            row
            for row in rows
            if abs(float(row["future_return"])) >= args.min_absolute_return
        ]
    groups = [("base", [])]
    for raw in args.group:
        name, separator, values = raw.partition("=")
        if not separator:
            raise ValueError("group must use NAME=FEATURE,FEATURE format")
        groups.append((name, _names(values)))
    split = int(len(rows) * 0.8)
    labels = np.asarray([int(row["label"]) for row in rows])
    for name, extra in groups:
        features = [*_names(args.base), *extra]
        x = np.asarray([[float(row[item]) for item in features] for row in rows])
        scaler = StandardScaler().fit(x[:split])
        classifier = LogisticRegression(
            C=args.inverse_regularization, max_iter=3000, random_state=42
        ).fit(scaler.transform(x[:split]), labels[:split])
        probabilities = classifier.predict_proba(scaler.transform(x[split:]))[:, 1]
        actual = labels[split:]
        print(
            f"{name}: features={len(features)} rows={len(rows)} validation={len(actual)} "
            f"accuracy={np.mean((probabilities >= 0.5) == actual):.4f} "
            f"brier={brier_score_loss(actual, probabilities):.4f} "
            f"auc={roc_auc_score(actual, probabilities):.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
