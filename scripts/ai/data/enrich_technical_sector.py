"""Add date-aligned sector ETF context to a technical candidate dataset."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.local_ai.market_features import build_market_training_rows  # noqa: E402
from app.local_ai.sector_features import (  # noqa: E402
    SECTOR_FEATURES,
    sector_etf,
    sector_features,
)
from app.providers import build_providers  # noqa: E402


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=1800)
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args()


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    with args.input.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    symbols = {row["symbol"].upper() for row in rows}
    etfs = sorted({sector_etf(symbol) for symbol in symbols})
    provider = build_providers(Settings())[0]
    candles_by_etf = {}
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(provider.get_candles, etf, args.limit): etf for etf in etfs
            }
            for future in as_completed(futures):
                etf = futures[future]
                candles_by_etf[etf] = future.result()
    finally:
        provider.close()
    features_by_etf = {
        etf: {
            datetime.fromisoformat(item.timestamp).date(): item.technical
            for item in build_market_training_rows(candles, horizon_days=1)
        }
        for etf, candles in candles_by_etf.items()
    }
    enriched = []
    for row in rows:
        etf = sector_etf(row["symbol"])
        date = datetime.fromisoformat(row["timestamp"]).date()
        context = features_by_etf.get(etf, {}).get(date)
        if context is None:
            continue
        stock = {name: float(row[name]) for name in ("return_5d", "sma_20_gap")}
        enriched.append({**row, **sector_features(stock, context)})
    fieldnames = [*rows[0], *SECTOR_FEATURES]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched)
    print(f"symbols={len(symbols)} etfs={len(etfs)} rows={len(enriched)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
