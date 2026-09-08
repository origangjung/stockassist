"""공시 후 수익률을 같은 날짜의 업종 또는 시장 중앙값과 비교해 재무 라벨을 만든다."""

import argparse
from collections import Counter, defaultdict
import csv
import json
import math
import os
from pathlib import Path
import statistics
import sys


ROOT = Path(__file__).resolve().parents[3]
DATASET_ROOT = (ROOT / "datasets").resolve()
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.collection_universe import COLLECTION_SYMBOLS_BY_SECTOR  # noqa: E402
from app.local_ai.financial_features import FINANCIAL_FEATURES  # noqa: E402


SYMBOL_SECTORS = {
    symbol: sector
    for sector, symbols in COLLECTION_SYMBOLS_BY_SECTOR.items()
    for symbol in symbols
}
OUTPUT_METADATA = (
    "feature_timestamp",
    "outcome_start_timestamp",
    "sector",
    "label_basis",
    "future_excess_return",
    "sector_neutral_future_return",
    "sample_weight",
)


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum-sector-peers", type=int, default=2)
    parser.add_argument("--minimum-market-peers", type=int, default=5)
    parser.add_argument("--minimum-absolute-return", type=float, default=0.0025)
    return parser.parse_args()


def _safe_output_path(value: Path) -> Path:
    """`_safe_output_path`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    path = value.expanduser().resolve()
    if path.suffix.casefold() != ".csv" or not path.is_relative_to(DATASET_ROOT):
        raise ValueError("output must be a CSV file inside the project datasets directory")
    return path


def _read(path: Path) -> list[dict[str, str]]:
    """`_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if not path.is_file() or path.is_symlink() or path.stat().st_size > 512 * 1024 * 1024:
        raise ValueError("input dataset is missing or invalid")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    required = {
        "timestamp",
        "symbol",
        "outcome_start_timestamp",
        "future_excess_return",
        *FINANCIAL_FEATURES,
    }
    if not rows or not required.issubset(rows[0]):
        raise ValueError("input dataset does not contain financial outcomes")
    return rows


def _deduplicate(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """같은 종목·결과 세션에는 결과 직전의 가장 최근 공시 특성만 남긴다."""

    selected: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        symbol = str(row["symbol"]).strip().upper()
        outcome_timestamp = str(row["outcome_start_timestamp"]).strip()
        if symbol not in SYMBOL_SECTORS or not outcome_timestamp:
            continue
        key = (outcome_timestamp, symbol)
        current = selected.get(key)
        if current is None or str(row["timestamp"]) > str(current["timestamp"]):
            selected[key] = row
    return sorted(
        selected.values(),
        key=lambda row: (str(row["outcome_start_timestamp"]), str(row["symbol"])),
    )


def relabel(
    rows: list[dict[str, str]],
    *,
    minimum_sector_peers: int,
    minimum_market_peers: int,
    minimum_absolute_return: float,
) -> tuple[list[dict[str, str | float | int]], dict[str, object]]:
    """동일 결과 날짜의 업종 중앙값을 우선 사용해 중립화된 이진 라벨을 계산한다."""

    if minimum_sector_peers < 2 or minimum_market_peers < 2:
        raise ValueError("peer minimums must be at least two")
    if not 0 <= minimum_absolute_return <= 0.2:
        raise ValueError("minimum absolute return is invalid")
    deduplicated = _deduplicate(rows)
    by_sector_date: dict[tuple[str, str], list[float]] = defaultdict(list)
    by_date: dict[str, list[float]] = defaultdict(list)
    parsed: list[tuple[dict[str, str], str, str, float]] = []
    for row in deduplicated:
        symbol = str(row["symbol"]).strip().upper()
        sector = SYMBOL_SECTORS[symbol]
        outcome_date = str(row["outcome_start_timestamp"])[:10]
        try:
            outcome = float(row["future_excess_return"])
            features = [float(row[name]) for name in FINANCIAL_FEATURES]
        except (TypeError, ValueError):
            continue
        if not math.isfinite(outcome) or not all(math.isfinite(value) for value in features):
            continue
        by_sector_date[(outcome_date, sector)].append(outcome)
        by_date[outcome_date].append(outcome)
        parsed.append((row, sector, outcome_date, outcome))

    labeled: list[dict[str, str | float | int]] = []
    basis_counts: Counter[str] = Counter()
    for row, sector, outcome_date, outcome in parsed:
        sector_values = by_sector_date[(outcome_date, sector)]
        market_values = by_date[outcome_date]
        if len(sector_values) >= minimum_sector_peers:
            reference = statistics.median(sector_values)
            basis = "sector_date_median"
        elif len(market_values) >= minimum_market_peers:
            reference = statistics.median(market_values)
            basis = "market_date_median"
        else:
            continue
        neutral_return = outcome - reference
        if abs(neutral_return) < minimum_absolute_return:
            continue
        basis_counts[basis] += 1
        labeled.append(
            {
                "timestamp": str(row["outcome_start_timestamp"]),
                "symbol": str(row["symbol"]).strip().upper(),
                **{name: row[name] for name in FINANCIAL_FEATURES},
                "feature_timestamp": str(row["timestamp"]),
                "outcome_start_timestamp": str(row["outcome_start_timestamp"]),
                "sector": sector,
                "label_basis": basis,
                "future_excess_return": outcome,
                "sector_neutral_future_return": neutral_return,
                "sample_weight": 0.0,
                "label": int(neutral_return > 0),
            }
        )

    date_counts = Counter(str(row["timestamp"])[:10] for row in labeled)
    if not labeled or not date_counts:
        raise ValueError("sector-neutral relabeling produced no rows")
    weight_scale = len(labeled) / len(date_counts)
    for row in labeled:
        row["sample_weight"] = weight_scale / date_counts[str(row["timestamp"])[:10]]
    labeled.sort(key=lambda row: (str(row["timestamp"]), str(row["symbol"])))
    report: dict[str, object] = {
        "source_rows": len(rows),
        "deduplicated_rows": len(deduplicated),
        "labeled_rows": len(labeled),
        "symbols": len({str(row["symbol"]) for row in labeled}),
        "outcome_dates": len(date_counts),
        "positive_rate": round(
            sum(int(row["label"]) for row in labeled) / len(labeled), 4
        ),
        "label_basis": dict(sorted(basis_counts.items())),
        "minimum_absolute_return": minimum_absolute_return,
    }
    return labeled, report


def write_rows(path: Path, rows: list[dict[str, str | float | int]]) -> None:
    """중립 라벨 데이터셋을 배타적 임시 파일에 쓴 뒤 원자 교체한다."""

    target = _safe_output_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    descriptor: int | None = None
    fieldnames = ["timestamp", "symbol", *FINANCIAL_FEATURES, *OUTPUT_METADATA, "label"]
    try:
        descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            descriptor = None
            writer = csv.DictWriter(stream, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    rows, report = relabel(
        _read(args.input),
        minimum_sector_peers=args.minimum_sector_peers,
        minimum_market_peers=args.minimum_market_peers,
        minimum_absolute_return=args.minimum_absolute_return,
    )
    write_rows(args.output, rows)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
