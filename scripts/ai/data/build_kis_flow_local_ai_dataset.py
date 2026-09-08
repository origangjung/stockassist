"""KIS 국내주식 일별 투자자 수급 후보 데이터셋을 구축한다."""

import argparse
import csv
from datetime import date, timedelta
from pathlib import Path
import shutil
import sys
import time


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.investor_flow.kis import KisInvestorFlowProvider  # noqa: E402
from app.local_ai.collection_universe import DEFAULT_KIS_FLOW_SYMBOLS  # noqa: E402
from app.local_ai.kis_flow_features import (  # noqa: E402
    KIS_FLOW_FEATURES,
    build_kis_flow_training_rows,
)
from app.providers import build_providers  # noqa: E402
from app.providers.errors import ProviderError  # noqa: E402


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", nargs="+", default=list(DEFAULT_KIS_FLOW_SYMBOLS))
    parser.add_argument("--end-date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--history-days", type=int, default=730)
    parser.add_argument("--horizon-days", type=int, default=10)
    parser.add_argument("--pages-per-request", type=int, default=10)
    parser.add_argument("--request-delay", type=float, default=0.12)
    parser.add_argument("--candle-limit", type=int, default=900)
    parser.add_argument("--benchmark-symbol", default="069500")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    if not 30 <= args.history_days <= 3650:
        raise ValueError("history-days must be between 30 and 3650")
    if not 1 <= args.horizon_days <= 60:
        raise ValueError("horizon-days must be between 1 and 60")
    if args.request_delay < 0.05:
        raise ValueError("request-delay must be at least 0.05 seconds")
    settings = Settings()
    app_key = settings.kis_app_key.get_secret_value().strip() if settings.kis_app_key else ""
    app_secret = (
        settings.kis_app_secret.get_secret_value().strip() if settings.kis_app_secret else ""
    )
    if not app_key or not app_secret:
        raise ValueError("KIS_APP_KEY and KIS_APP_SECRET are required")
    stock_provider = build_providers(settings)[0]
    kis = KisInvestorFlowProvider.create(
        base_url=settings.kis_base_url,
        app_key=app_key,
        app_secret=app_secret,
        timeout_seconds=settings.kis_timeout_seconds,
    )
    target = args.output_dir / "investor_flow.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = _load_compatible_rows(
        target,
        horizon_days=args.horizon_days,
        resume=args.resume,
    )
    all_rows = {(row["timestamp"], row["symbol"]): row for row in existing}
    failures: list[str] = []
    try:
        benchmark = stock_provider.get_candles(args.benchmark_symbol, args.candle_limit)
        for symbol in [value.strip() for value in args.symbols]:
            try:
                flows = _collect_history(kis, symbol, args)
                candles = stock_provider.get_candles(symbol, args.candle_limit)
                rows = build_kis_flow_training_rows(
                    flows,
                    candles,
                    benchmark_candles=benchmark,
                    horizon_days=args.horizon_days,
                )
            except (ProviderError, ValueError) as exc:
                failures.append(f"{symbol}:{type(exc).__name__}")
                continue
            for row in rows:
                values = {
                    **row,
                    "symbol": symbol,
                    "horizon_days": args.horizon_days,
                }
                all_rows[(values["timestamp"], symbol)] = values
            _write_rows(target, list(all_rows.values()))
            print(f"completed_symbol={symbol} flow_days={len(flows)} rows={len(rows)}", flush=True)
    finally:
        kis.close()
        stock_provider.close()
    _write_rows(target, list(all_rows.values()))
    print(f"total_rows={len(all_rows)} failed={','.join(failures) or 'none'}")
    return 0 if all_rows else 2


def _collect_history(
    kis: KisInvestorFlowProvider, symbol: str, args: argparse.Namespace
) -> list:
    """`_collect_history`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    cutoff = args.end_date
    earliest = cutoff - timedelta(days=args.history_days)
    collected = {}
    while cutoff >= earliest:
        try:
            batch = kis.get_daily_flows(
                symbol, end_date=cutoff, max_pages=args.pages_per_request
            )
        except ProviderError:
            # KIS가 제공하는 과거 범위를 넘긴 경우에도 앞서 받은 정상 구간은 보존한다.
            if collected:
                break
            raise
        if not batch:
            break
        for row in batch:
            if row.trade_date >= earliest:
                collected[row.trade_date] = row
        oldest = min(row.trade_date for row in batch)
        if oldest <= earliest or oldest >= cutoff:
            break
        cutoff = oldest - timedelta(days=1)
        time.sleep(args.request_delay)
    return [collected[key] for key in sorted(collected)]


def _fieldnames() -> list[str]:
    """`_fieldnames`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return [
        "timestamp",
        "symbol",
        *KIS_FLOW_FEATURES,
        "future_return",
        "benchmark_future_return",
        "future_excess_return",
        "horizon_days",
        "label",
    ]


def _read_rows(path: Path) -> list[dict]:
    """`_read_rows`은(는) 필요한 데이터를 조회해 반환합니다."""

    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        # 피처 스키마가 확장된 경우 구형 행의 빈 열을 그대로 재사용하면
        # 학습 데이터에 결측치가 남으므로 완전한 현재 스키마 행만 이어받는다.
        return [
            row
            for row in csv.DictReader(source)
            if all(str(row.get(name) or "").strip() for name in KIS_FLOW_FEATURES)
        ]


def _load_compatible_rows(
    path: Path,
    *,
    horizon_days: int,
    resume: bool,
) -> list[dict]:
    """동일 기간 데이터만 이어받고 기존 기간 파일은 별도로 보관한다."""

    rows = _read_rows(path)
    if not rows:
        return []
    horizons = {int(row.get("horizon_days") or 5) for row in rows}
    if len(horizons) != 1:
        raise ValueError(f"mixed prediction horizons in {path}: {sorted(horizons)}")
    existing_horizon = horizons.pop()
    if existing_horizon != horizon_days:
        archive = path.with_name(f"{path.stem}-legacy-{existing_horizon}d.csv")
        if not archive.exists():
            temporary = archive.with_suffix(archive.suffix + ".tmp")
            shutil.copyfile(path, temporary)
            temporary.replace(archive)
        return []
    if not resume:
        return []
    for row in rows:
        row["horizon_days"] = str(existing_horizon)
    return rows


def _write_rows(path: Path, rows: list[dict]) -> None:
    """`_write_rows`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    rows.sort(key=lambda row: (row["timestamp"], row["symbol"]))
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=_fieldnames())
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


if __name__ == "__main__":
    raise SystemExit(main())
