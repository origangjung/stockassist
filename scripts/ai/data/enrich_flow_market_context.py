"""Join past-only price context into FINRA investor-flow training rows."""

import argparse
import csv
from datetime import datetime
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.flow_market_features import (  # noqa: E402
    FLOW_MARKET_FEATURES,
    flow_market_features,
)
from app.local_ai.market_features import TECHNICAL_FEATURES  # noqa: E402


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--flow", type=Path, required=True)
    parser.add_argument("--market", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def _key(row: dict[str, str]) -> tuple[str, object]:
    """`_key`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return row["symbol"].upper(), datetime.fromisoformat(row["timestamp"]).date()


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    with args.market.open("r", encoding="utf-8-sig", newline="") as source:
        market_rows = list(csv.DictReader(source))
    market_by_key = {
        _key(row): {name: float(row[name]) for name in TECHNICAL_FEATURES}
        for row in market_rows
    }
    with args.flow.open("r", encoding="utf-8-sig", newline="") as source:
        flow_rows = list(csv.DictReader(source))
    enriched = [
        {**row, **flow_market_features(market_by_key[_key(row)])}
        for row in flow_rows
        if _key(row) in market_by_key
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=[*flow_rows[0], *FLOW_MARKET_FEATURES])
        writer.writeheader()
        writer.writerows(enriched)
    print(f"input={len(flow_rows)} matched={len(enriched)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
