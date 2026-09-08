"""Add deterministic ETF asset-class one-hot features to a training CSV."""

import argparse
import csv
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.etf import (  # noqa: E402
    ETF_ASSET_CLASS_FEATURES,
    etf_asset_class_features,
)


MAX_DATASET_BYTES = 512 * 1024 * 1024


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description="Add ETF asset-class features")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    if not args.input.is_file() or args.input.stat().st_size > MAX_DATASET_BYTES:
        raise ValueError("input dataset is missing or exceeds the size limit")
    with args.input.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        rows = list(reader)
        original_names = reader.fieldnames or []
    if not rows or not {"timestamp", "symbol", "label"}.issubset(original_names):
        raise ValueError("input dataset is missing required columns")

    fieldnames = [
        name for name in original_names if name not in ETF_ASSET_CLASS_FEATURES
    ]
    label_position = fieldnames.index("label")
    fieldnames[label_position:label_position] = ETF_ASSET_CLASS_FEATURES
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(f"{args.output.suffix}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, **etf_asset_class_features(row["symbol"])})
    temporary.replace(args.output)
    print(f"rows={len(rows)} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
