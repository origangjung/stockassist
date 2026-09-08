"""SEC 연간 공시와 공시 직전 종가로 재무 학습 데이터에 PIT 밸류에이션을 추가한다."""

import argparse
from bisect import bisect_left, bisect_right
import csv
from datetime import date
import json
import math
import os
from pathlib import Path
import sys
import time

import httpx2


ROOT = Path(__file__).resolve().parents[3]
DATASET_ROOT = (ROOT / "datasets").resolve()
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.local_ai.financial_features import (  # noqa: E402
    AnnualValuationSnapshot,
    extract_annual_valuation_snapshots,
)
from app.local_ai.sec import SecCompanyFactsClient  # noqa: E402


PIT_VALUATION_FEATURES = (
    "pit_per_signed_log",
    "pit_pbr_signed_log",
    "pit_psr_signed_log",
    "pit_roe_signed_log",
)
PIT_VALUATION_METADATA = (
    "valuation_filed",
    "valuation_price_timestamp",
    "pit_per",
    "pit_pbr",
    "pit_psr",
    "pit_roe",
)
MAX_INPUT_BYTES = 512 * 1024 * 1024


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--market-data", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--request-delay", type=float, default=0.15)
    parser.add_argument("--roe-only", action="store_true")
    return parser.parse_args()


def _safe_output_path(value: Path) -> Path:
    """`_safe_output_path`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    path = value.expanduser().resolve()
    if path.suffix.casefold() != ".csv" or not path.is_relative_to(DATASET_ROOT):
        raise ValueError("output must be a CSV file inside the project datasets directory")
    return path


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """`_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    resolved = path.expanduser().resolve()
    if (
        not resolved.is_file()
        or resolved.is_symlink()
        or resolved.stat().st_size > MAX_INPUT_BYTES
    ):
        raise ValueError(f"invalid input dataset: {path.name}")
    with resolved.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        return list(reader.fieldnames or []), list(reader)


def build_price_index(
    rows: list[dict[str, str]],
) -> dict[str, tuple[list[date], list[float]]]:
    """종목별 거래일 종가를 정렬하고 중복 날짜는 마지막 행으로 확정한다."""

    grouped: dict[str, dict[date, float]] = {}
    for row in rows:
        try:
            symbol = str(row["symbol"]).strip().upper()
            timestamp = date.fromisoformat(str(row["timestamp"])[:10])
            close_price = float(row["close_price"])
        except (KeyError, TypeError, ValueError):
            continue
        if not symbol or not math.isfinite(close_price) or close_price <= 0:
            continue
        grouped.setdefault(symbol, {})[timestamp] = close_price
    result = {}
    for symbol, values in grouped.items():
        dates = sorted(values)
        result[symbol] = (dates, [values[item] for item in dates])
    return result


def enrich_rows(
    rows: list[dict[str, str]],
    annuals_by_symbol: dict[str, list[AnnualValuationSnapshot]],
    price_index: dict[str, tuple[list[date], list[float]]],
) -> tuple[list[dict[str, str | float]], dict[str, int | float]]:
    """각 공시 시점보다 앞서 공개·확정된 연간 재무와 종가만 결합한다."""

    enriched: list[dict[str, str | float]] = []
    missing_annual = 0
    missing_shares = 0
    missing_price = 0
    invalid_ratio = 0
    for row in rows:
        symbol = str(row.get("symbol") or "").strip().upper()
        raw_feature_timestamp = str(row.get("feature_timestamp") or row.get("timestamp") or "")
        try:
            feature_date = date.fromisoformat(raw_feature_timestamp[:10])
        except ValueError:
            continue
        annuals = annuals_by_symbol.get(symbol, [])
        annual_dates = [item.filed for item in annuals]
        annual_position = bisect_right(annual_dates, feature_date) - 1
        if annual_position < 0:
            missing_annual += 1
            continue
        annual = annuals[annual_position]
        if annual.shares_outstanding is None or annual.shares_outstanding <= 0:
            missing_shares += 1
            continue
        prices = price_index.get(symbol)
        if prices is None:
            missing_price += 1
            continue
        price_dates, price_values = prices
        # 같은 날짜의 장 마감보다 공시가 먼저였을 수 있으므로 직전 거래일만 허용한다.
        price_position = bisect_left(price_dates, feature_date) - 1
        if price_position < 0:
            missing_price += 1
            continue
        price = price_values[price_position]
        market_cap = price * annual.shares_outstanding
        if not all(
            math.isfinite(value) and value != 0
            for value in (market_cap, annual.revenue, annual.net_income, annual.equity)
        ):
            invalid_ratio += 1
            continue
        ratios = {
            "pit_per": market_cap / annual.net_income,
            "pit_pbr": market_cap / annual.equity,
            "pit_psr": market_cap / annual.revenue,
            "pit_roe": annual.net_income / annual.equity,
        }
        if not all(math.isfinite(value) for value in ratios.values()):
            invalid_ratio += 1
            continue
        enriched.append(
            {
                **row,
                **{
                    f"{name}_signed_log": _signed_log(value)
                    for name, value in ratios.items()
                },
                "valuation_filed": annual.filed.isoformat(),
                "valuation_price_timestamp": price_dates[price_position].isoformat(),
                **ratios,
            }
        )
    report: dict[str, int | float] = {
        "source_rows": len(rows),
        "enriched_rows": len(enriched),
        "coverage": round(len(enriched) / len(rows), 4) if rows else 0.0,
        "missing_annual": missing_annual,
        "missing_shares": missing_shares,
        "missing_price": missing_price,
        "invalid_ratio": invalid_ratio,
    }
    return enriched, report


def enrich_roe_rows(
    rows: list[dict[str, str]],
    annuals_by_symbol: dict[str, list[AnnualValuationSnapshot]],
) -> tuple[list[dict[str, str | float]], dict[str, int | float]]:
    """가격 이력 없이도 계산 가능한 최신 공개 연간 ROE만 시점 기준으로 결합한다."""

    enriched: list[dict[str, str | float]] = []
    missing_annual = 0
    invalid_ratio = 0
    for row in rows:
        symbol = str(row.get("symbol") or "").strip().upper()
        raw_timestamp = str(row.get("feature_timestamp") or row.get("timestamp") or "")
        try:
            feature_date = date.fromisoformat(raw_timestamp[:10])
        except ValueError:
            continue
        annuals = annuals_by_symbol.get(symbol, [])
        position = bisect_right([item.filed for item in annuals], feature_date) - 1
        if position < 0:
            missing_annual += 1
            continue
        annual = annuals[position]
        if annual.equity == 0:
            invalid_ratio += 1
            continue
        roe = annual.net_income / annual.equity
        if not math.isfinite(roe):
            invalid_ratio += 1
            continue
        enriched.append(
            {
                **row,
                "pit_roe_signed_log": _signed_log(roe),
                "valuation_filed": annual.filed.isoformat(),
                "pit_roe": roe,
            }
        )
    return enriched, {
        "source_rows": len(rows),
        "enriched_rows": len(enriched),
        "coverage": round(len(enriched) / len(rows), 4) if rows else 0.0,
        "missing_annual": missing_annual,
        "invalid_ratio": invalid_ratio,
    }


def _signed_log(value: float) -> float:
    """`_signed_log`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return math.copysign(math.log1p(abs(value)), value)


def _write(
    path: Path,
    original_fields: list[str],
    rows: list[dict[str, str | float]],
    *,
    feature_fields: tuple[str, ...] = PIT_VALUATION_FEATURES,
    metadata_fields: tuple[str, ...] = PIT_VALUATION_METADATA,
) -> None:
    """`_write`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    target = _safe_output_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    descriptor: int | None = None
    fields = [
        *[name for name in original_fields if name not in feature_fields],
        *feature_fields,
        *metadata_fields,
    ]
    try:
        descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            descriptor = None
            writer = csv.DictWriter(stream, fieldnames=fields)
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
    original_fields, rows = _read(args.input)
    if not rows or not {"timestamp", "symbol", "label"}.issubset(original_fields):
        raise ValueError("financial input has an invalid schema")
    market_rows: list[dict[str, str]] = []
    if not args.roe_only:
        if args.market_data is None:
            raise ValueError("market-data is required unless --roe-only is used")
        _, market_rows = _read(args.market_data)
        if not market_rows or not {
            "timestamp",
            "symbol",
            "close_price",
        }.issubset(market_rows[0]):
            raise ValueError("market input must contain point-in-time close_price")
    symbols = sorted({str(row["symbol"]).strip().upper() for row in rows})
    settings = Settings()
    user_agent = (settings.sec_user_agent or "").strip()
    if not user_agent:
        raise ValueError("SEC_USER_AGENT is required")
    client = SecCompanyFactsClient(user_agent=user_agent, base_url=settings.sec_base_url)
    annuals_by_symbol: dict[str, list[AnnualValuationSnapshot]] = {}
    failures: list[str] = []
    try:
        for symbol in symbols:
            try:
                annuals_by_symbol[symbol] = extract_annual_valuation_snapshots(
                    client.companyfacts(symbol)
                )
            except (ValueError, httpx2.HTTPError):
                failures.append(symbol)
            finally:
                client.release_cached_symbol(symbol)
            time.sleep(max(args.request_delay, 0.1))
    finally:
        client.close()
    if args.roe_only:
        enriched, report = enrich_roe_rows(rows, annuals_by_symbol)
    else:
        enriched, report = enrich_rows(
            rows, annuals_by_symbol, build_price_index(market_rows)
        )
    if not enriched:
        raise ValueError("PIT valuation enrichment produced no rows")
    if args.roe_only:
        _write(
            args.output,
            original_fields,
            enriched,
            feature_fields=("pit_roe_signed_log",),
            metadata_fields=("valuation_filed", "pit_roe"),
        )
    else:
        _write(args.output, original_fields, enriched)
    print(json.dumps({**report, "failed_symbols": failures}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
