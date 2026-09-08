"""Relabel an existing FINRA dataset for future short-pressure increase."""

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description="Relabel the local FINRA flow dataset")
    parser.add_argument("--path", type=Path, required=True)
    parser.add_argument("--horizon-days", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    with args.path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        rows = list(reader)
        fieldnames = reader.fieldnames
    if not fieldnames or args.horizon_days < 1:
        raise ValueError("dataset and positive horizon_days are required")
    by_symbol: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_symbol[row["symbol"]].append(row)
    relabeled = []
    for symbol_rows in by_symbol.values():
        symbol_rows.sort(key=lambda row: row["timestamp"])
        for index in range(len(symbol_rows) - args.horizon_days):
            current = float(symbol_rows[index]["short_volume_ratio"])
            future = sum(
                float(row["short_volume_ratio"])
                for row in symbol_rows[index + 1 : index + args.horizon_days + 1]
            ) / args.horizon_days
            symbol_rows[index]["label"] = str(int(future > current))
            relabeled.append(symbol_rows[index])
    relabeled.sort(key=lambda row: (row["timestamp"], row["symbol"]))
    with args.path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(relabeled)
    print(f"investor_flow={len(relabeled)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
