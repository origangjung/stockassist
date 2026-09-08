"""Build a point-in-time financial dataset from SEC 10-Q company facts."""

import argparse
import csv
from pathlib import Path
import sys
import time

import httpx2


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.local_ai.financial_features import (  # noqa: E402
    FINANCIAL_FEATURES,
    build_financial_training_rows,
)
from app.local_ai.sec import SecCompanyFactsClient  # noqa: E402


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description="Build the SEC financial dataset")
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--request-delay", type=float, default=0.15)
    parser.add_argument("--max-rows-per-symbol", type=int, default=24)
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def merge_rows(existing: list[dict], incoming: list[dict]) -> list[dict]:
    """`merge_rows`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    merged = {
        (str(row["timestamp"]), str(row["symbol"]).strip().upper()): row
        for row in [*existing, *incoming]
    }
    return sorted(merged.values(), key=lambda row: (row["timestamp"], row["symbol"]))


def _write_rows(path: Path, rows: list[dict]) -> None:
    """`_write_rows`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(
            output, fieldnames=["timestamp", "symbol", *FINANCIAL_FEATURES, "label"]
        )
        writer.writeheader()
        writer.writerows(rows)
    for attempt in range(5):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.2 * (attempt + 1))


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    settings = Settings()
    user_agent = (settings.sec_user_agent or "").strip()
    if not user_agent:
        raise ValueError("SEC_USER_AGENT is required")
    client = SecCompanyFactsClient(
        user_agent=user_agent,
        base_url=settings.sec_base_url,
    )
    rows: list[dict] = []
    failures: list[str] = []
    try:
        for raw_symbol in args.symbols:
            symbol = raw_symbol.strip().upper()
            try:
                company_rows = build_financial_training_rows(client.companyfacts(symbol))
            except (ValueError, httpx2.HTTPError):
                failures.append(symbol)
                continue
            finally:
                client.release_cached_symbol(symbol)
            if args.max_rows_per_symbol > 0:
                company_rows = company_rows[-args.max_rows_per_symbol :]
            rows.extend({**row, "symbol": symbol} for row in company_rows)
            time.sleep(max(args.request_delay, 0.1))
    finally:
        client.close()
    target = args.output_dir / "financial.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict] = []
    if target.is_file() and not args.replace:
        with target.open("r", encoding="utf-8-sig", newline="") as source:
            existing = list(csv.DictReader(source))
    merged = merge_rows(existing, rows)
    _write_rows(target, merged)
    print(
        f"financial={len(merged)} collected={len(rows)} "
        f"failed_symbols={','.join(failures) or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
