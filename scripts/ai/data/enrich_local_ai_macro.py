"""Add point-in-time FRED macro features to market specialist datasets."""

import argparse
import csv
from datetime import date, datetime, timedelta
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
DATASET_ROOT = (ROOT / "datasets").resolve()
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.local_ai.fred import FredClient  # noqa: E402
from app.local_ai.macro_features import (  # noqa: E402
    MACRO_FEATURES,
    macro_features_at,
)


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description="Enrich local market AI data with FRED")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def safe_data_dir(path: Path, *, must_exist: bool) -> Path:
    """거시 데이터 입출력 경로를 Git 제외 datasets 루트 안으로 제한한다."""

    resolved = path.expanduser().resolve()
    if (
        not resolved.is_relative_to(DATASET_ROOT)
        or resolved == DATASET_ROOT
        or resolved.is_symlink()
        or (must_exist and not resolved.is_dir())
    ):
        raise ValueError("macro data directory must remain below datasets")
    return resolved


def _read(path: Path) -> list[dict]:
    """`_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def _row_date(row: dict) -> date:
    """`_row_date`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return datetime.fromisoformat(str(row["timestamp"])).date()


def _write_atomic(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    """완성된 PIT 거시 CSV만 원자적으로 공개한다."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    data_dir = safe_data_dir(args.data_dir, must_exist=True)
    output_dir = safe_data_dir(args.output_dir or args.data_dir, must_exist=False)
    paths = [data_dir / "technical.csv", data_dir / "risk.csv"]
    if any(not path.is_file() or path.is_symlink() for path in paths):
        raise ValueError("technical.csv and risk.csv are required")
    if args.dry_run:
        print(
            f"macro_enrichment=planned input={data_dir.name} output={output_dir.name}"
        )
        return 0
    settings = Settings()
    api_key = settings.fred_api_key.get_secret_value().strip() if settings.fred_api_key else ""
    if not api_key:
        raise ValueError("FRED_API_KEY is required")
    datasets = {path: _read(path) for path in paths}
    dates = sorted({_row_date(row) for rows in datasets.values() for row in rows})
    client = FredClient(api_key=api_key, base_url=settings.fred_base_url)
    try:
        observations = client.macro_observations(
            observation_start=min(dates) - timedelta(days=60),
            observation_end=max(dates),
        )
    finally:
        client.close()
    features_by_date = {
        day: values
        for day in dates
        if (values := macro_features_at(observations, day)) is not None
    }
    for path, rows in datasets.items():
        enriched = []
        for row in rows:
            values = features_by_date.get(_row_date(row))
            if values is not None:
                enriched.append({**row, **values})
        if not enriched:
            raise ValueError(f"{path.name}: no complete point-in-time macro rows")
        fieldnames = list(rows[0])
        for name in MACRO_FEATURES:
            if name not in fieldnames:
                fieldnames.insert(-1, name)
        _write_atomic(output_dir / path.name, fieldnames, enriched)
        print(f"{path.name}={len(enriched)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
