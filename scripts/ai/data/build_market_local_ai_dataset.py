"""Build leakage-aware local AI datasets from real provider-adjusted candles."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import os
from pathlib import Path
import sys
import time

import httpx2


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.local_ai.market_features import (  # noqa: E402
    BENCHMARK_TECHNICAL_FEATURES,
    LONG_HORIZON_RISK_FEATURES,
    RISK_FEATURES,
    TECHNICAL_FEATURES,
    build_market_training_rows,
)
from app.providers import build_providers  # noqa: E402
from app.providers.errors import ProviderError  # noqa: E402


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description="Build technical and risk training datasets")
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument("--limit", type=int, default=365)
    parser.add_argument("--horizon-days", type=int, default=5)
    parser.add_argument("--technical-horizon-days", type=int)
    parser.add_argument("--risk-horizon-days", type=int)
    parser.add_argument("--outcome-horizon-days", type=int, action="append", default=[])
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--benchmark-symbol", default="SPY")
    parser.add_argument("--technical-min-return", type=float, default=0.0)
    parser.add_argument("--technical-min-excess-return", type=float, default=0.0)
    parser.add_argument("--risk-threshold", type=float, default=-0.03)
    parser.add_argument("--include-long-horizon-risk", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    return parser.parse_args()


def write_rows(
    path: Path,
    names: tuple[str, ...],
    rows: list[dict],
    *,
    extra_names: tuple[str, ...] = (),
) -> None:
    """`write_rows`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(
                target,
                fieldnames=["timestamp", "symbol", *names, *extra_names, "label"],
            )
            writer.writeheader()
            writer.writerows(rows)
            target.flush()
            os.fsync(target.fileno())
        for attempt in range(5):
            try:
                os.replace(temporary, path)
                break
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.2 * (attempt + 1))
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    if not 50 <= args.limit <= 5000:
        raise ValueError("limit must be between 50 and 5000")
    if not 1 <= args.workers <= 8:
        raise ValueError("workers must be between 1 and 8")
    technical_horizon = args.technical_horizon_days or args.horizon_days
    risk_horizon = args.risk_horizon_days or args.horizon_days
    horizons = {technical_horizon, risk_horizon, *args.outcome_horizon_days}
    if any(not 1 <= value <= 60 for value in horizons):
        raise ValueError("market horizons must be between 1 and 60 trading days")
    provider = build_providers(Settings())[0]
    technical_rows: list[dict] = []
    risk_rows: list[dict] = []
    outcome_rows: dict[int, list[dict]] = {
        horizon: [] for horizon in args.outcome_horizon_days
    }
    try:
        benchmark_candles = provider.get_candles(args.benchmark_symbol.upper(), args.limit)
        symbols = [raw_symbol.strip().upper() for raw_symbol in args.symbols]
        candles_by_symbol = {}
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(provider.get_candles, symbol, args.limit): symbol
                for symbol in symbols
            }
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    candles_by_symbol[symbol] = future.result()
                except (ValueError, httpx2.HTTPError, ProviderError):
                    print(f"skipped_symbol={symbol}", file=sys.stderr)
        for symbol in symbols:
            candles = candles_by_symbol.get(symbol)
            if not candles:
                continue
            rows_by_horizon = {
                horizon: build_market_training_rows(
                    candles,
                    horizon_days=horizon,
                    risk_threshold=args.risk_threshold,
                    benchmark_candles=benchmark_candles,
                    include_long_horizon_risk=(
                        args.include_long_horizon_risk and horizon == risk_horizon
                    ),
                )
                for horizon in horizons
            }
            for row in rows_by_horizon[technical_horizon]:
                outcome = (
                    row.future_excess_return
                    if row.future_excess_return is not None
                    else row.future_return
                )
                if (
                    abs(row.future_return) >= args.technical_min_return
                    and abs(outcome) >= args.technical_min_excess_return
                ):
                    technical_rows.append(
                        {
                            "timestamp": row.timestamp,
                            "symbol": symbol,
                            **row.technical,
                            "close_price": row.close_price,
                            "future_return": row.future_return,
                            "benchmark_future_return": row.benchmark_future_return,
                            "future_excess_return": row.future_excess_return,
                            "horizon_days": technical_horizon,
                            "label": row.technical_label,
                        }
                    )
            for row in rows_by_horizon[risk_horizon]:
                risk_rows.append(
                    {
                        "timestamp": row.timestamp,
                        "symbol": symbol,
                        **row.risk,
                        "future_max_drawdown": row.future_max_drawdown,
                        "horizon_days": risk_horizon,
                        "label": row.risk_label,
                    }
                )
            for horizon, target_rows in outcome_rows.items():
                target_rows.extend(
                    {
                        "timestamp": row.timestamp,
                        "symbol": symbol,
                        "future_return": row.future_return,
                        "benchmark_future_return": row.benchmark_future_return,
                        "future_excess_return": row.future_excess_return,
                        "future_max_drawdown": row.future_max_drawdown,
                        "horizon_days": horizon,
                        "label": row.technical_label,
                    }
                    for row in rows_by_horizon[horizon]
                )
    finally:
        provider.close()
    technical_rows.sort(key=lambda row: (row["timestamp"], row["symbol"]))
    risk_rows.sort(key=lambda row: (row["timestamp"], row["symbol"]))
    write_rows(
        args.output_dir / "technical.csv",
        (*TECHNICAL_FEATURES, *BENCHMARK_TECHNICAL_FEATURES),
        technical_rows,
        extra_names=(
            "close_price",
            "future_return",
            "benchmark_future_return",
            "future_excess_return",
            "horizon_days",
        ),
    )
    write_rows(
        args.output_dir / "risk.csv",
        (
            (*RISK_FEATURES, *LONG_HORIZON_RISK_FEATURES)
            if args.include_long_horizon_risk
            else RISK_FEATURES
        ),
        risk_rows,
        extra_names=("future_max_drawdown", "horizon_days"),
    )
    for horizon, rows in outcome_rows.items():
        rows.sort(key=lambda row: (row["timestamp"], row["symbol"]))
        write_rows(
            args.output_dir / f"outcomes-{horizon}.csv",
            (),
            rows,
            extra_names=(
                "future_return",
                "benchmark_future_return",
                "future_excess_return",
                "future_max_drawdown",
                "horizon_days",
            ),
        )
    print(
        f"technical={len(technical_rows)} technical_horizon={technical_horizon} "
        f"risk={len(risk_rows)} risk_horizon={risk_horizon} "
        f"outcome_horizons={','.join(map(str, sorted(outcome_rows))) or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
