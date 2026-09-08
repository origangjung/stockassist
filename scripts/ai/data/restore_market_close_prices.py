"""최근 조정종가 앵커와 기존 일간 수익률로 과거 종가를 복원한다."""

import argparse
import csv
from datetime import date
import json
import math
import os
from pathlib import Path
import sys

import httpx2


ROOT = Path(__file__).resolve().parents[3]
DATASET_ROOT = (ROOT / "datasets").resolve()
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.providers import build_providers  # noqa: E402
from app.providers.errors import ProviderError  # noqa: E402


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--symbols", nargs="*", default=[])
    parser.add_argument("--anchor-limit", type=int, default=60)
    return parser.parse_args()


def restore_symbol_rows(
    rows: list[dict[str, str]], anchors: dict[date, float]
) -> list[dict[str, str | float]]:
    """겹치는 실제 종가 한 점을 기준으로 수익률 체인을 앞뒤로 복원한다."""

    restored, _ = restore_symbol_rows_with_diagnostics(rows, anchors)
    return restored


def restore_symbol_rows_with_diagnostics(
    rows: list[dict[str, str]], anchors: dict[date, float]
) -> tuple[list[dict[str, str | float]], float | None]:
    """복원 결과와 겹치는 실제 종가 대비 최대 상대 오차를 반환한다."""

    ordered = sorted(rows, key=lambda row: str(row["timestamp"]))
    if not ordered or not anchors:
        return [], None
    dates = [date.fromisoformat(str(row["timestamp"])[:10]) for row in ordered]
    overlap = [index for index, item in enumerate(dates) if item in anchors]
    if not overlap:
        return [], None
    anchor_index = overlap[-1]
    closes: list[float | None] = [None] * len(ordered)
    closes[anchor_index] = anchors[dates[anchor_index]]
    for index in range(anchor_index, 0, -1):
        daily_return = float(ordered[index]["return_1d"])
        denominator = 1 + daily_return
        if not math.isfinite(denominator) or denominator <= 0:
            return [], None
        closes[index - 1] = float(closes[index]) / denominator
    for index in range(anchor_index + 1, len(ordered)):
        daily_return = float(ordered[index]["return_1d"])
        if not math.isfinite(daily_return) or 1 + daily_return <= 0:
            return [], None
        closes[index] = float(closes[index - 1]) * (1 + daily_return)
    # 최근 겹침 구간에서 제공자 값과 복원값이 달라지면 가격 기준이 바뀐 것이므로 폐기한다.
    maximum_error = max(
        abs(float(closes[index]) / anchors[dates[index]] - 1) for index in overlap
    )
    if maximum_error > 1e-5:
        return [], maximum_error
    return (
        [{**row, "close_price": float(closes[index])} for index, row in enumerate(ordered)],
        maximum_error,
    )


def _safe_path(value: Path, *, output: bool) -> Path:
    """`_safe_path`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    path = value.expanduser().resolve()
    if path.suffix.casefold() != ".csv":
        raise ValueError("dataset path must be a CSV file")
    if output and not path.is_relative_to(DATASET_ROOT):
        raise ValueError("output must remain inside the project datasets directory")
    return path


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """`_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    source_path = _safe_path(path, output=False)
    if not source_path.is_file() or source_path.is_symlink():
        raise ValueError("input market dataset is invalid")
    with source_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    if not rows or not {"timestamp", "symbol", "return_1d"}.issubset(fields):
        raise ValueError("input market dataset has an invalid schema")
    return fields, rows


def _write(path: Path, fields: list[str], rows: list[dict[str, str | float]]) -> None:
    """`_write`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    target = _safe_path(path, output=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    descriptor: int | None = None
    output_fields = [name for name in fields if name != "close_price"]
    insert_at = output_fields.index("symbol") + 1
    output_fields.insert(insert_at, "close_price")
    try:
        descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            descriptor = None
            writer = csv.DictWriter(stream, fieldnames=output_fields)
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
    if not 20 <= args.anchor_limit <= 200:
        raise ValueError("anchor-limit must be between 20 and 200")
    fields, rows = _read(args.input)
    available = {str(row["symbol"]).strip().upper() for row in rows}
    requested = {value.strip().upper() for value in args.symbols if value.strip()}
    symbols = sorted(available & requested) if requested else sorted(available)
    grouped = {
        symbol: [row for row in rows if str(row["symbol"]).strip().upper() == symbol]
        for symbol in symbols
    }
    provider = build_providers(Settings())[0]
    restored: list[dict[str, str | float]] = []
    failures: list[str] = []
    basis_mismatch: dict[str, float] = {}
    try:
        for symbol in symbols:
            try:
                candles = provider.get_candles(symbol, args.anchor_limit)
                anchors = {item.timestamp.date(): float(item.close) for item in candles}
                symbol_rows, maximum_error = restore_symbol_rows_with_diagnostics(
                    grouped[symbol], anchors
                )
            except (ValueError, httpx2.HTTPError, ProviderError):
                symbol_rows = []
                maximum_error = None
            if symbol_rows:
                restored.extend(symbol_rows)
            else:
                failures.append(symbol)
                if maximum_error is not None:
                    basis_mismatch[symbol] = round(maximum_error, 6)
    finally:
        provider.close()
    restored.sort(key=lambda row: (str(row["timestamp"]), str(row["symbol"])))
    report = {
        "symbols": len(symbols),
        "restored_symbols": len(symbols) - len(failures),
        "restored_rows": len(restored),
        "failed_symbols": failures,
        "basis_mismatch": basis_mismatch,
    }
    print(json.dumps(report, ensure_ascii=True, indent=2))
    if not restored:
        raise ValueError("close-price restoration produced no rows")
    _write(args.output, fields, restored)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
