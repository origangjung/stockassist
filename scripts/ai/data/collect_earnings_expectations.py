"""Alpha Vantage 분기 EPS 예상치 기록을 무료 한도 안에서 증분 저장한다."""

import argparse
import csv
from datetime import date, timedelta
import os
from pathlib import Path
import sys
import time

import httpx2


ROOT = Path(__file__).resolve().parents[3]
DATASET_ROOT = (ROOT / "datasets").resolve()
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.local_ai.collection_universe import DEFAULT_COLLECTION_SYMBOLS  # noqa: E402
from app.local_ai.earnings_expectations import AlphaVantageEarningsClient  # noqa: E402
from app.local_ai.http_security import validate_symbol  # noqa: E402


FIELDS = (
    "symbol",
    "fiscal_date",
    "reported_date",
    "available_date",
    "reported_eps",
    "estimated_eps",
    "eps_surprise",
    "eps_surprise_percentage",
    "report_time",
    "retrieved_date",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", nargs="*")
    parser.add_argument(
        "--output",
        type=Path,
        default=DATASET_ROOT / "local-ai-incremental" / "earnings" / "earnings.csv",
    )
    parser.add_argument("--max-symbols", type=int, default=25)
    parser.add_argument("--refresh-days", type=int, default=21)
    parser.add_argument("--request-interval-seconds", type=float, default=2.0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def safe_output_path(value: Path) -> Path:
    """출력 CSV를 프로젝트 데이터셋 내부의 일반 파일로 제한한다."""

    path = value.expanduser().resolve()
    if (
        path.suffix.casefold() != ".csv"
        or not path.is_relative_to(DATASET_ROOT)
        or path.is_symlink()
    ):
        raise ValueError("earnings output must be a CSV inside datasets")
    return path


def load_rows(path: Path) -> list[dict[str, str]]:
    """기존 구조화 기록만 읽고 원시 공급자 응답은 사용하지 않는다."""

    if not path.is_file():
        return []
    if path.is_symlink() or path.stat().st_size > 128 * 1024 * 1024:
        raise ValueError("existing earnings dataset is invalid")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not set(FIELDS).issubset(reader.fieldnames or []):
            raise ValueError("existing earnings dataset has an invalid schema")
        return list(reader)


def save_rows(path: Path, rows: list[dict[str, str]]) -> None:
    """종목·분기 중복을 제거하고 임시 파일을 거쳐 원자적으로 저장한다."""

    merged = {
        (str(row["symbol"]), str(row["fiscal_date"])): row
        for row in rows
    }
    ordered = sorted(merged.values(), key=lambda row: (row["symbol"], row["fiscal_date"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(ordered)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def symbols_due(
    symbols: tuple[str, ...],
    rows: list[dict[str, str]],
    *,
    today: date,
    refresh_days: int,
    force: bool,
) -> list[str]:
    """미수집 또는 갱신 주기가 지난 종목만 원래 순서대로 반환한다."""

    if not 7 <= refresh_days <= 90:
        raise ValueError("refresh-days must be between 7 and 90")
    latest: dict[str, date] = {}
    for row in rows:
        try:
            retrieved = date.fromisoformat(row["retrieved_date"])
            symbol = validate_symbol(row["symbol"])
        except (KeyError, ValueError):
            continue
        latest[symbol] = max(latest.get(symbol, date.min), retrieved)
    cutoff = today - timedelta(days=refresh_days)
    return [
        symbol
        for symbol in symbols
        if force or symbol not in latest or latest[symbol] <= cutoff
    ]


def main() -> int:
    args = parse_args()
    if not 1 <= args.max_symbols <= 25:
        raise ValueError("max-symbols must remain within the free daily limit")
    if not 0 <= args.request_interval_seconds <= 60:
        raise ValueError("request interval must be between 0 and 60 seconds")
    symbols = tuple(
        dict.fromkeys(
            validate_symbol(symbol)
            for symbol in (args.symbols or DEFAULT_COLLECTION_SYMBOLS)
        )
    )
    output = safe_output_path(args.output)
    existing = load_rows(output)
    pending = symbols_due(
        symbols,
        existing,
        today=date.today(),
        refresh_days=args.refresh_days,
        force=args.force,
    )
    selected = pending[: args.max_symbols]
    if args.dry_run:
        print(
            f"earnings_collection=planned selected={len(selected)} "
            f"remaining={max(0, len(pending) - len(selected))}"
        )
        return 0
    settings = Settings()
    api_key = (
        settings.alpha_vantage_api_key.get_secret_value().strip()
        if settings.alpha_vantage_api_key
        else ""
    )
    if not api_key:
        raise ValueError("ALPHA_VANTAGE_API_KEY is required")
    client = AlphaVantageEarningsClient(
        api_key=api_key,
        base_url=settings.alpha_vantage_base_url,
        timeout_seconds=settings.news_timeout_seconds,
        daily_request_limit=settings.alpha_vantage_daily_request_limit,
    )
    new_rows: list[dict[str, str]] = []
    failures: list[str] = []
    try:
        for index, symbol in enumerate(selected):
            try:
                snapshots = client.quarterly(symbol)
            except (ValueError, httpx2.HTTPError):
                failures.append(symbol)
                continue
            finally:
                if index + 1 < len(selected) and args.request_interval_seconds:
                    time.sleep(args.request_interval_seconds)
            retrieved = date.today().isoformat()
            new_rows.extend(
                {
                    "symbol": symbol,
                    "fiscal_date": item.fiscal_date.isoformat(),
                    "reported_date": item.reported_date.isoformat(),
                    "available_date": item.available_date.isoformat(),
                    "reported_eps": str(item.reported_eps),
                    "estimated_eps": str(item.estimated_eps),
                    "eps_surprise": str(item.surprise),
                    "eps_surprise_percentage": str(item.surprise_percentage),
                    "report_time": item.report_time,
                    "retrieved_date": retrieved,
                }
                for item in snapshots
            )
    finally:
        client.close()
    save_rows(output, [*existing, *new_rows])
    print(
        f"earnings_collection=ok requested={len(selected)} rows={len(new_rows)} "
        f"failed={','.join(failures) or 'none'} automatic_training=false"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
