"""Build a FINRA short-volume specialist dataset aligned to Toss candles."""

import argparse
import csv
from datetime import datetime
from pathlib import Path
import shutil
import sys
import time

import httpx2


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.local_ai.finra import FinraShortVolumeClient  # noqa: E402
from app.local_ai.flow_features import FLOW_FEATURES, build_flow_training_rows  # noqa: E402
from app.local_ai.flow_market_features import (  # noqa: E402
    FLOW_MARKET_FEATURES,
    flow_market_features,
)
from app.local_ai.market_features import build_market_training_rows  # noqa: E402
from app.providers import build_providers  # noqa: E402
from app.providers.errors import ProviderError  # noqa: E402


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description="Build the FINRA investor-flow dataset")
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument("--limit", type=int, default=365)
    parser.add_argument("--horizon-days", type=int, default=5)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--include-market-context", action="store_true")
    parser.add_argument("--minimum-absolute-excess-return", type=float, default=0.005)
    parser.add_argument("--benchmark-symbol", default="SPY")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def _fieldnames(include_market_context: bool) -> list[str]:
    """`_fieldnames`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return [
        "timestamp",
        "symbol",
        *FLOW_FEATURES,
        *(FLOW_MARKET_FEATURES if include_market_context else ()),
        "future_return",
        "benchmark_future_return",
        "future_excess_return",
        "horizon_days",
        "label",
    ]


def _write_rows(path: Path, rows: list[dict], *, include_market_context: bool) -> None:
    """`_write_rows`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=_fieldnames(include_market_context),
        )
        writer.writeheader()
        writer.writerows(rows)
    for attempt in range(5):
        try:
            temporary.replace(path)
            break
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.2 * (attempt + 1))


def _load_compatible_rows(
    target: Path,
    *,
    horizon_days: int,
    include_market_context: bool,
    resume: bool,
) -> list[dict]:
    """기간이 일치할 때만 이어받고, 이전 기간 데이터는 손실 없이 보관한다."""

    if not target.is_file():
        return []
    with target.open("r", encoding="utf-8-sig", newline="") as source:
        existing = list(csv.DictReader(source))
    if not existing:
        return []
    horizons = {int(row.get("horizon_days") or 5) for row in existing}
    if len(horizons) != 1:
        raise ValueError(f"mixed prediction horizons in {target}: {sorted(horizons)}")
    existing_horizon = horizons.pop()
    if existing_horizon != horizon_days:
        archive = target.with_name(f"{target.stem}-legacy-{existing_horizon}d.csv")
        if not archive.exists():
            temporary = archive.with_suffix(archive.suffix + ".tmp")
            shutil.copyfile(target, temporary)
            temporary.replace(archive)
        return []
    if not resume:
        return []
    rows: list[dict] = []
    for row in existing:
        row["horizon_days"] = str(existing_horizon)
        rows.append({name: row[name] for name in _fieldnames(include_market_context)})
    return rows


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    settings = Settings()
    client_id = (settings.finra_client_id or "").strip()
    client_secret = (
        settings.finra_client_secret.get_secret_value().strip()
        if settings.finra_client_secret
        else ""
    )
    if not client_id or not client_secret:
        raise ValueError("FINRA_CLIENT_ID and FINRA_CLIENT_SECRET are required")
    stock_provider = build_providers(settings)[0]
    finra = FinraShortVolumeClient(
        base_url=settings.finra_api_base_url,
        token_url=settings.finra_token_url,
        client_id=client_id,
        client_secret=client_secret,
    )
    target = args.output_dir / "investor_flow.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = _load_compatible_rows(
        target,
        horizon_days=args.horizon_days,
        include_market_context=args.include_market_context,
        resume=args.resume,
    )
    completed = {str(row["symbol"]).upper() for row in rows}
    failures: list[str] = []
    try:
        benchmark_candles = stock_provider.get_candles(
            args.benchmark_symbol.upper(), args.limit
        )
        for raw_symbol in args.symbols:
            symbol = raw_symbol.strip().upper()
            if symbol in completed:
                continue
            try:
                records = finra.records(symbol)
                candles = stock_provider.get_candles(symbol, args.limit)
            except (ValueError, httpx2.HTTPError, ProviderError):
                failures.append(symbol)
                continue
            market_by_date = {
                datetime.fromisoformat(item.timestamp).date(): item.technical
                for item in build_market_training_rows(candles, horizon_days=1)
            }
            for row in build_flow_training_rows(
                records,
                candles,
                horizon_days=args.horizon_days,
                minimum_absolute_excess_return=args.minimum_absolute_excess_return,
                benchmark_candles=benchmark_candles,
            ):
                values = {
                    **row,
                    "symbol": symbol,
                    "horizon_days": args.horizon_days,
                }
                if args.include_market_context:
                    market = market_by_date.get(
                        datetime.fromisoformat(str(row["timestamp"])).date()
                    )
                    if market is None:
                        continue
                    values.update(flow_market_features(market))
                rows.append(values)
            rows.sort(key=lambda row: (row["timestamp"], row["symbol"]))
            _write_rows(
                target, rows, include_market_context=args.include_market_context
            )
            completed.add(symbol)
            print(f"completed_symbol={symbol} total_rows={len(rows)}", flush=True)
    finally:
        finra.close()
        stock_provider.close()
    rows.sort(key=lambda row: (row["timestamp"], row["symbol"]))
    _write_rows(target, rows, include_market_context=args.include_market_context)
    print(f"investor_flow={len(rows)} failed_symbols={','.join(failures) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
