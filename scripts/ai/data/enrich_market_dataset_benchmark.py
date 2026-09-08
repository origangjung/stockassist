"""Add SPY-relative features to an existing local market dataset."""

import argparse
import csv
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.local_ai.market_features import (  # noqa: E402
    BENCHMARK_TECHNICAL_FEATURES,
    RISK_FEATURES,
    build_market_training_rows,
)
from app.providers import build_providers  # noqa: E402


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description="Add benchmark-relative market features")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--benchmark-symbol", default="SPY")
    parser.add_argument("--limit", type=int, default=1500)
    return parser.parse_args()


def _read(path: Path) -> list[dict]:
    """`_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def _write(path: Path, additions: tuple[str, ...], rows: list[dict]) -> None:
    """`_write`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    fieldnames = list(rows[0])
    for name in additions:
        if name not in fieldnames:
            fieldnames.insert(-1, name)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    provider = build_providers(Settings())[0]
    try:
        candles = provider.get_candles(args.benchmark_symbol.upper(), args.limit)
    finally:
        provider.close()
    benchmark_rows = build_market_training_rows(candles)
    technical = {row.timestamp: row.technical for row in benchmark_rows}
    risk = {row.timestamp: row.risk for row in benchmark_rows}
    technical_rows = _read(args.data_dir / "technical.csv")
    for row in technical_rows:
        values = technical.get(row["timestamp"])
        if values:
            row.update(
                market_return_5d=values["return_5d"],
                market_sma_20_gap=values["sma_20_gap"],
                relative_return_5d=float(row["return_5d"]) - values["return_5d"],
                relative_sma_20_gap=float(row["sma_20_gap"])
                - values["sma_20_gap"],
            )
    technical_rows = [
        row for row in technical_rows if set(BENCHMARK_TECHNICAL_FEATURES).issubset(row)
    ]
    risk_rows = _read(args.data_dir / "risk.csv")
    for row in risk_rows:
        values = risk.get(row["timestamp"])
        if values:
            row.update(
                market_volatility_20=values["volatility_20"],
                relative_volatility_20=float(row["volatility_20"])
                - values["volatility_20"],
            )
    risk_rows = [row for row in risk_rows if set(RISK_FEATURES).issubset(row)]
    _write(args.data_dir / "technical.csv", BENCHMARK_TECHNICAL_FEATURES, technical_rows)
    _write(args.data_dir / "risk.csv", RISK_FEATURES, risk_rows)
    print(f"technical={len(technical_rows)} risk={len(risk_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
