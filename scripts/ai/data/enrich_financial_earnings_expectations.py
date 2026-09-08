"""PIT 분기 EPS 예상치 특성을 기존 재무 후보 행에 결합한다."""

import argparse
from bisect import bisect_right
import csv
from datetime import date
import math
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DATASET_ROOT = (ROOT / "datasets").resolve()


FEATURES = (
    "eps_surprise_signed_log",
    "eps_surprise_positive",
    "eps_yoy_growth_signed_log",
    "eps_yoy_available",
    "eps_beat_streak_scaled",
)
METADATA = (
    "earnings_fiscal_date",
    "earnings_reported_date",
    "earnings_available_date",
    "earnings_report_time",
    "reported_eps",
    "estimated_eps",
    "eps_surprise",
    "eps_surprise_percentage",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--financial", type=Path, required=True)
    parser.add_argument("--earnings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def enrich_rows(
    financial_rows: list[dict[str, str]],
    earnings_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str | float]], dict[str, int | float]]:
    """각 재무 행보다 늦지 않게 공개된 가장 최근 예상치 기록만 결합한다."""

    histories: dict[str, list[dict[str, str | float | date]]] = {}
    for row in earnings_rows:
        try:
            symbol = row["symbol"].strip().upper()
            item = {
                **row,
                "_available": date.fromisoformat(row["available_date"]),
                "_reported_eps": float(row["reported_eps"]),
                "_surprise_pct": float(row["eps_surprise_percentage"]),
            }
        except (KeyError, TypeError, ValueError):
            continue
        if all(math.isfinite(float(item[key])) for key in ("_reported_eps", "_surprise_pct")):
            histories.setdefault(symbol, []).append(item)
    for values in histories.values():
        values.sort(key=lambda item: (item["_available"], item["fiscal_date"]))
        _add_history_features(values)

    enriched: list[dict[str, str | float]] = []
    missing = 0
    for row in financial_rows:
        symbol = str(row.get("symbol") or "").strip().upper()
        try:
            feature_date = date.fromisoformat(str(row.get("timestamp") or "")[:10])
        except ValueError:
            continue
        history = histories.get(symbol, [])
        position = bisect_right([item["_available"] for item in history], feature_date) - 1
        if position < 0:
            missing += 1
            continue
        item = history[position]
        enriched.append(
            {
                **row,
                **{name: item[name] for name in FEATURES},
                "earnings_fiscal_date": item["fiscal_date"],
                "earnings_reported_date": item["reported_date"],
                "earnings_available_date": item["available_date"],
                "earnings_report_time": item["report_time"],
                "reported_eps": item["reported_eps"],
                "estimated_eps": item["estimated_eps"],
                "eps_surprise": item["eps_surprise"],
                "eps_surprise_percentage": item["eps_surprise_percentage"],
            }
        )
    return enriched, {
        "source_rows": len(financial_rows),
        "enriched_rows": len(enriched),
        "coverage": round(len(enriched) / len(financial_rows), 4)
        if financial_rows
        else 0.0,
        "missing_prior_earnings": missing,
    }


def _add_history_features(values: list[dict[str, str | float | date]]) -> None:
    """과거 분기만 사용해 전년 대비 EPS와 연속 서프라이즈 특성을 계산한다."""

    streak = 0
    for index, item in enumerate(values):
        surprise_pct = float(item["_surprise_pct"])
        positive = surprise_pct > 0
        streak = max(1, streak + 1) if positive else min(-1, streak - 1)
        yoy_available = index >= 4 and float(values[index - 4]["_reported_eps"]) != 0
        yoy_growth = 0.0
        if yoy_available:
            previous = float(values[index - 4]["_reported_eps"])
            yoy_growth = (float(item["_reported_eps"]) - previous) / abs(previous)
        item.update(
            {
                "eps_surprise_signed_log": math.copysign(
                    math.log1p(abs(surprise_pct) / 100.0), surprise_pct
                ),
                "eps_surprise_positive": float(positive),
                "eps_yoy_growth_signed_log": math.copysign(
                    math.log1p(abs(yoy_growth)), yoy_growth
                ),
                "eps_yoy_available": float(yoy_available),
                "eps_beat_streak_scaled": max(-1.0, min(1.0, streak / 4.0)),
            }
        )


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    resolved = path.resolve()
    if not resolved.is_file() or resolved.is_symlink():
        raise ValueError("input CSV is unavailable")
    with resolved.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        return list(reader.fieldnames or []), list(reader)


def _write(path: Path, fields: list[str], rows: list[dict[str, str | float]]) -> None:
    target = path.resolve()
    if (
        target.suffix.casefold() != ".csv"
        or not target.is_relative_to(DATASET_ROOT)
        or target.is_symlink()
    ):
        raise ValueError("financial expectations output must be a CSV inside datasets")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    generated = {*FEATURES, *METADATA}
    output_fields = [*[field for field in fields if field not in generated], *FEATURES, *METADATA]
    try:
        with temporary.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=output_fields)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    args = parse_args()
    fields, financial = _read(args.financial)
    _, earnings = _read(args.earnings)
    rows, report = enrich_rows(financial, earnings)
    _write(args.output, fields, rows)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
