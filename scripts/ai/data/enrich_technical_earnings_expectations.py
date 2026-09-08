"""기술 AI 일별 행에 당시 공개된 가장 최근 실적 예상·발표 정보를 결합한다."""

import argparse
import csv
from datetime import date
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
DATASET_ROOT = (ROOT / "datasets").resolve()
sys.path.insert(0, str(ROOT))

from scripts.ai.data.enrich_financial_earnings_expectations import (  # noqa: E402
    FEATURES as EARNINGS_FEATURES,
    METADATA as EARNINGS_METADATA,
    enrich_rows,
)


EVENT_FEATURES = (
    "earnings_age_log_scaled",
    "earnings_event_3d",
    "earnings_event_10d",
)


def parse_args() -> argparse.Namespace:
    """기술 데이터, 실적 데이터와 안전한 출력 경로를 읽는다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--technical", type=Path, required=True)
    parser.add_argument("--earnings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def enrich_technical_rows(
    technical_rows: list[dict[str, str]],
    earnings_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str | float]], dict[str, int | float]]:
    """미래 발표를 제외하고 최근 실적과 발표 후 경과일 피처를 결합한다."""

    for row in technical_rows:
        try:
            date.fromisoformat(str(row["timestamp"])[:10])
            symbol = str(row["symbol"]).strip()
        except (KeyError, ValueError) as exc:
            raise ValueError("technical row has an invalid timestamp or symbol") from exc
        if not symbol:
            raise ValueError("technical row has an invalid timestamp or symbol")
    enriched, report = enrich_rows(technical_rows, earnings_rows)
    result: list[dict[str, str | float]] = []
    for row in enriched:
        feature_date = date.fromisoformat(str(row["timestamp"])[:10])
        available_date = date.fromisoformat(str(row["earnings_available_date"]))
        age = (feature_date - available_date).days
        if age < 0:
            raise ValueError("future earnings information reached a technical row")
        result.append(
            {
                **row,
                "earnings_age_log_scaled": min(
                    1.0, math.log1p(age) / math.log1p(365)
                ),
                "earnings_event_3d": float(age <= 3),
                "earnings_event_10d": float(age <= 10),
            }
        )
    report.update(
        {
            "event_rows_3d": sum(
                int(float(row["earnings_event_3d"])) for row in result
            ),
            "event_rows_10d": sum(
                int(float(row["earnings_event_10d"])) for row in result
            ),
        }
    )
    return result, report


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """심볼릭 링크와 과대 파일을 거부하고 구조화된 CSV를 읽는다."""

    resolved = path.resolve()
    if (
        not resolved.is_file()
        or resolved.is_symlink()
        or resolved.stat().st_size > 256 * 1024 * 1024
    ):
        raise ValueError("input CSV is unavailable or unsafe")
    with resolved.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        return list(reader.fieldnames or []), list(reader)


def _write(
    path: Path,
    fields: list[str],
    rows: list[dict[str, str | float]],
) -> None:
    """완성된 후보 CSV만 datasets 내부에 원자적으로 공개한다."""

    target = path.resolve()
    if (
        target.suffix.casefold() != ".csv"
        or not target.is_relative_to(DATASET_ROOT)
        or target.is_symlink()
    ):
        raise ValueError("technical earnings output must be a CSV inside datasets")
    generated = {*EARNINGS_FEATURES, *EARNINGS_METADATA, *EVENT_FEATURES}
    output_fields = [
        *[field for field in fields if field not in generated],
        *EARNINGS_FEATURES,
        *EVENT_FEATURES,
        *EARNINGS_METADATA,
    ]
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=output_fields)
            writer.writeheader()
            writer.writerows(rows)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    """실적 후보를 생성하되 운영 모델 학습이나 승격은 수행하지 않는다."""

    args = parse_args()
    fields, technical = _read(args.technical)
    _, earnings = _read(args.earnings)
    rows, report = enrich_technical_rows(technical, earnings)
    _write(args.output, fields, rows)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
