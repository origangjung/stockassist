"""수급·위험 데이터에 Qlib식 동일 시점 횡단면 특성을 추가한다."""

import argparse
import csv
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.cross_section_features import enrich_cross_section_rows  # noqa: E402


FEATURES = {
    "investor_flow": (
        "short_volume_ratio",
        "short_ratio_change_5d",
        "reported_volume_ratio_20d",
        "price_return_5d",
        "price_volatility_20",
    ),
    "risk": (
        "volatility_20",
        "drawdown_20",
        "downside_deviation_20",
        "range_width_20",
        "relative_volatility_20",
    ),
}


def parse_args() -> argparse.Namespace:
    """명령행에서 대상 전문 AI와 입출력 경로를 읽는다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=sorted(FEATURES), required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    """원본을 보존하면서 횡단면 특성이 추가된 후보 CSV를 생성한다."""

    args = parse_args()
    with args.input.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        rows = list(reader)
        input_fields = reader.fieldnames or []
    required = {"timestamp", "symbol", "label", *FEATURES[args.dataset]}
    if not rows or not required.issubset(input_fields):
        raise ValueError("input dataset is empty or missing required columns")
    enriched, output_names = enrich_cross_section_rows(rows, FEATURES[args.dataset])
    if not enriched:
        raise ValueError("no timestamp contains at least five comparable symbols")
    fieldnames = [name for name in input_fields if name != "label"]
    fieldnames.extend(name for name in output_names if name not in fieldnames)
    fieldnames.append("label")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched)
    temporary.replace(args.output)
    print(
        f"dataset={args.dataset} rows={len(enriched)} "
        f"features={len(output_names)} symbols={len({row['symbol'] for row in enriched})}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
