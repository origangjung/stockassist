"""PIT 밸류에이션용 Toss 조정 일봉을 종목별 체크포인트로 수집한다."""

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys

import httpx2


ROOT = Path(__file__).resolve().parents[3]
DATASET_ROOT = (ROOT / "datasets").resolve()
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.providers import build_providers  # noqa: E402
from app.providers.contracts import Candle, StockProvider  # noqa: E402
from app.providers.errors import ProviderError  # noqa: E402


SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.-]{1,10}$")
SYMBOL_FIELDS = ("timestamp", "symbol", "close_price", "price_basis")


@dataclass(frozen=True)
class RequiredRange:
    """`RequiredRange` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    first: date
    last: date


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--financial-data", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=1700)
    parser.add_argument("--max-symbols", type=int, default=0)
    return parser.parse_args()


def required_ranges(rows: list[dict[str, str]]) -> dict[str, RequiredRange]:
    """재무 행마다 가격이 필요한 공시일 범위를 종목별로 계산한다."""

    grouped: dict[str, list[date]] = {}
    for row in rows:
        symbol = str(row.get("symbol") or "").strip().upper()
        raw_timestamp = str(row.get("feature_timestamp") or row.get("timestamp") or "")
        try:
            timestamp = date.fromisoformat(raw_timestamp[:10])
        except ValueError:
            continue
        if SYMBOL_PATTERN.fullmatch(symbol):
            grouped.setdefault(symbol, []).append(timestamp)
    if not grouped:
        raise ValueError("financial dataset has no valid symbol timestamps")
    return {
        symbol: RequiredRange(min(values), max(values))
        for symbol, values in sorted(grouped.items())
    }


def validated_history(
    candles: list[Candle], required: RequiredRange
) -> list[Candle] | None:
    """중복이 없고 필요한 공시 범위를 덮는 검증된 조정 일봉만 반환한다."""

    ordered = sorted(candles, key=lambda item: item.timestamp)
    dates = [item.timestamp.date() for item in ordered]
    if (
        not ordered
        or len(dates) != len(set(dates))
        or any(item.price_basis != "provider_adjusted" for item in ordered)
        or any(item.close <= 0 for item in ordered)
        or dates[0] >= required.first
        or dates[-1] < required.last
    ):
        return None
    return ordered


def _safe_output_dir(value: Path) -> Path:
    """`_safe_output_dir`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    path = value.expanduser().resolve()
    if not path.is_relative_to(DATASET_ROOT) or path == DATASET_ROOT or path.is_symlink():
        raise ValueError("output directory must remain inside the project datasets directory")
    return path


def _read_financial(path: Path) -> list[dict[str, str]]:
    """`_read_financial`은(는) 필요한 데이터를 조회해 반환합니다."""

    resolved = path.expanduser().resolve()
    if not resolved.is_file() or resolved.is_symlink() or resolved.stat().st_size > 512 * 1024 * 1024:
        raise ValueError("financial dataset is invalid")
    with resolved.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows or not {"timestamp", "symbol"}.issubset(rows[0]):
        raise ValueError("financial dataset has an invalid schema")
    return rows


def _read_symbol(path: Path, symbol: str, required: RequiredRange) -> list[dict[str, str]]:
    """`_read_symbol`은(는) 필요한 데이터를 조회해 반환합니다."""

    if not path.is_file() or path.is_symlink() or path.stat().st_size > 16 * 1024 * 1024:
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows or not set(SYMBOL_FIELDS).issubset(rows[0]):
        return []
    try:
        dates = [date.fromisoformat(str(row["timestamp"])[:10]) for row in rows]
        valid = (
            all(row["symbol"] == symbol for row in rows)
            and dates == sorted(set(dates))
            and dates[0] < required.first
            and dates[-1] >= required.last
            and all(
                row["price_basis"] == "provider_adjusted"
                and Decimal(row["close_price"]) > 0
                for row in rows
            )
        )
    except (ArithmeticError, KeyError, ValueError):
        return []
    return rows if valid else []


def _atomic_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """`_atomic_csv`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor: int | None = None
    try:
        descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            descriptor = None
            writer = csv.DictWriter(stream, fieldnames=SYMBOL_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    """`_atomic_json`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor: int | None = None
    try:
        descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = None
            json.dump(payload, stream, ensure_ascii=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def _collect_symbol(
    provider: StockProvider,
    symbol: str,
    required: RequiredRange,
    limit: int,
) -> list[dict[str, object]]:
    """`_collect_symbol`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    candles = validated_history(provider.get_candles(symbol, limit), required)
    if candles is None:
        return []
    return [
        {
            "timestamp": item.timestamp.isoformat(),
            "symbol": symbol,
            "close_price": str(item.close),
            "price_basis": item.price_basis,
        }
        for item in candles
    ]


def _manifest(
    output_dir: Path,
    ranges: dict[str, RequiredRange],
) -> tuple[dict[str, object], list[dict[str, str]]]:
    """`_manifest`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    files: dict[str, object] = {}
    combined: list[dict[str, str]] = []
    for symbol, required in ranges.items():
        path = output_dir / "symbols" / f"{symbol}.csv"
        rows = _read_symbol(path, symbol, required)
        if not rows:
            continue
        combined.extend(rows)
        files[symbol] = {
            "rows": len(rows),
            "first": rows[0]["timestamp"],
            "last": rows[-1]["timestamp"],
            "sha256": sha256(path.read_bytes()).hexdigest(),
            "required": {
                key: value.isoformat() for key, value in asdict(required).items()
            },
        }
    combined.sort(key=lambda row: (row["timestamp"], row["symbol"]))
    return (
        {
            "status": "complete" if len(files) == len(ranges) else "partial",
            "required_symbols": len(ranges),
            "completed_symbols": len(files),
            "remaining_symbols": sorted(set(ranges) - set(files)),
            "files": files,
        },
        combined,
    )


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    if not 200 <= args.limit <= 5000 or not 0 <= args.max_symbols <= 90:
        raise ValueError("collection limits are invalid")
    ranges = required_ranges(_read_financial(args.financial_data))
    output_dir = _safe_output_dir(args.output_dir)
    symbol_dir = output_dir / "symbols"
    symbol_dir.mkdir(parents=True, exist_ok=True)
    pending = [
        symbol
        for symbol, required in ranges.items()
        if not _read_symbol(symbol_dir / f"{symbol}.csv", symbol, required)
    ]
    selected = pending[: args.max_symbols] if args.max_symbols else pending
    provider = build_providers(Settings())[0]
    policy = provider.candle_price_basis_policy
    if policy.expected_basis != "provider_adjusted" or policy.verification_status != "verified":
        provider.close()
        raise ValueError("provider adjusted-price policy is not verified")
    failed: list[str] = []
    try:
        for symbol in selected:
            try:
                rows = _collect_symbol(provider, symbol, ranges[symbol], args.limit)
            except (ValueError, httpx2.HTTPError, ProviderError):
                rows = []
            if rows:
                _atomic_csv(symbol_dir / f"{symbol}.csv", rows)
            else:
                failed.append(symbol)
    finally:
        provider.close()
    manifest, combined = _manifest(output_dir, ranges)
    manifest["attempted_symbols"] = selected
    manifest["failed_symbols"] = failed
    _atomic_json(output_dir / "manifest.json", manifest)
    if manifest["status"] == "complete":
        _atomic_csv(output_dir / "market-close.csv", combined)
    print(json.dumps(manifest, ensure_ascii=True, indent=2))
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
