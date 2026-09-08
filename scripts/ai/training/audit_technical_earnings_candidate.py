"""기술 AI 실적 이벤트 후보의 커버리지와 시점 안전성을 감사한다."""

import argparse
import csv
from datetime import date
import json
import math
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DATASET_ROOT = (ROOT / "datasets").resolve()
REQUIRED_FEATURES = (
    "eps_surprise_signed_log",
    "eps_surprise_positive",
    "eps_yoy_growth_signed_log",
    "eps_yoy_available",
    "eps_beat_streak_scaled",
    "earnings_age_log_scaled",
    "earnings_event_3d",
    "earnings_event_10d",
)


def parse_args() -> argparse.Namespace:
    """후보·원본 CSV와 감사 보고서 경로를 읽는다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def _read(path: Path) -> list[dict[str, str]]:
    """심볼릭 링크와 과대 입력을 거부하고 CSV를 읽는다."""

    resolved = path.resolve()
    if (
        not resolved.is_file()
        or resolved.is_symlink()
        or resolved.stat().st_size > 512 * 1024 * 1024
    ):
        raise ValueError("audit input is unavailable or unsafe")
    with resolved.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def audit(
    candidate_rows: list[dict[str, str]],
    source_rows: list[dict[str, str]],
) -> dict[str, object]:
    """누수·구조 검사를 수행하고 검증 준비 여부와 사유를 반환한다."""

    reasons: list[str] = []
    required = {
        "timestamp",
        "symbol",
        "future_excess_return",
        "horizon_days",
        "earnings_available_date",
        *REQUIRED_FEATURES,
    }
    if not candidate_rows or not required.issubset(candidate_rows[0]):
        return {
            "status": "collect_more_data",
            "rows": len(candidate_rows),
            "source_rows": len(source_rows),
            "reasons": ["missing_rows_or_required_columns"],
        }

    keys: set[tuple[str, str]] = set()
    timestamps: list[str] = []
    symbols: set[str] = set()
    event_rows = 0
    invalid_rows = 0
    future_leakage_rows = 0
    duplicate_rows = 0
    for row in candidate_rows:
        try:
            timestamp = str(row["timestamp"])
            feature_date = date.fromisoformat(timestamp[:10])
            available = date.fromisoformat(row["earnings_available_date"])
            symbol = row["symbol"].strip().upper()
            horizon = int(row["horizon_days"])
            values = [float(row[name]) for name in REQUIRED_FEATURES]
            outcome = float(row["future_excess_return"])
            if (
                not symbol
                or horizon != 10
                or not all(math.isfinite(value) for value in [*values, outcome])
            ):
                raise ValueError
        except (KeyError, TypeError, ValueError):
            invalid_rows += 1
            continue
        key = (timestamp, symbol)
        if key in keys:
            duplicate_rows += 1
        keys.add(key)
        if available > feature_date:
            future_leakage_rows += 1
        timestamps.append(timestamp)
        symbols.add(symbol)
        event_rows += int(float(row["earnings_event_10d"]) == 1.0)

    unique_timestamps = len(set(timestamps))
    coverage = len(candidate_rows) / len(source_rows) if source_rows else 0.0
    if timestamps != sorted(timestamps):
        reasons.append("timestamps_not_sorted")
    if invalid_rows:
        reasons.append("invalid_rows")
    if duplicate_rows:
        reasons.append("duplicate_rows")
    if future_leakage_rows:
        reasons.append("future_earnings_leakage")
    if len(candidate_rows) < 10_000:
        reasons.append("rows_below_10000")
    if unique_timestamps < 500:
        reasons.append("timestamps_below_500")
    if len(symbols) < 20:
        reasons.append("symbols_below_20")
    if event_rows < 200:
        reasons.append("event_rows_10d_below_200")
    if coverage < 0.2:
        reasons.append("source_coverage_below_20pct")
    return {
        "status": "ready_for_validation" if not reasons else "collect_more_data",
        "rows": len(candidate_rows),
        "source_rows": len(source_rows),
        "coverage": round(coverage, 4),
        "symbols": len(symbols),
        "unique_timestamps": unique_timestamps,
        "date_start": min(timestamps) if timestamps else None,
        "date_end": max(timestamps) if timestamps else None,
        "event_rows_10d": event_rows,
        "invalid_rows": invalid_rows,
        "duplicate_rows": duplicate_rows,
        "future_leakage_rows": future_leakage_rows,
        "reasons": reasons,
    }


def save_report(path: Path, report: dict[str, object]) -> None:
    """감사 보고서를 datasets 내부에 원자적으로 저장한다."""

    target = path.resolve()
    if (
        target.suffix.casefold() != ".json"
        or not target.is_relative_to(DATASET_ROOT)
        or target.is_symlink()
    ):
        raise ValueError("audit output must be JSON inside datasets")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    """후보를 감사해 보고서를 저장하며 준비 부족 자체는 오류로 처리하지 않는다."""

    args = parse_args()
    report = audit(_read(args.candidate), _read(args.source))
    save_report(args.output, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
