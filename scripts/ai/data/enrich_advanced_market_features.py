"""기존 기술 학습 CSV에서 누수 없는 고급 OHLCV 후보 데이터셋을 만든다."""

import argparse
import csv
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.advanced_market_features import (  # noqa: E402
    ADVANCED_TECHNICAL_FEATURES,
    enrich_advanced_technical_rows,
)


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    with args.input.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        rows = list(reader)
        input_fields = reader.fieldnames or []
    required = {"timestamp", "symbol", "close_price", "return_5d", "volatility_20"}
    if not rows or not required.issubset(input_fields):
        raise ValueError("input technical dataset is empty or missing required columns")

    enriched = enrich_advanced_technical_rows(rows)
    if not enriched:
        raise ValueError("no symbol has enough history for advanced features")
    fields = [name for name in input_fields if name != "label"]
    fields.extend(name for name in ADVANCED_TECHNICAL_FEATURES if name not in fields)
    fields.append("label")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(enriched)
    print(
        f"rows={len(enriched)} symbols={len({row['symbol'] for row in enriched})} "
        f"features={len(ADVANCED_TECHNICAL_FEATURES)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
