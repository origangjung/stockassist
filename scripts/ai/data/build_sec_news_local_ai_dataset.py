"""시점 정렬된 SEC 8-K 이벤트를 뉴스·공시 AI 후보 데이터셋으로 변환한다."""

import argparse
import csv
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
DATASET_ROOT = (ROOT / "datasets").resolve()
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.sec_event_features import SEC_EVENT_FEATURES  # noqa: E402


OUTCOME_FIELDS = (
    "future_return",
    "benchmark_future_return",
    "future_excess_return",
)


def parse_args() -> argparse.Namespace:
    """명령행 입력과 출력 디렉터리를 읽는다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def safe_dataset_path(path: Path, *, directory: bool = False) -> Path:
    """생성 데이터가 프로젝트 datasets 루트 밖으로 나가지 않게 제한한다."""

    resolved = path.expanduser().resolve()
    if not resolved.is_relative_to(DATASET_ROOT) or resolved == DATASET_ROOT:
        raise ValueError("dataset path must stay below datasets")
    if not directory and (not resolved.is_file() or resolved.is_symlink()):
        raise ValueError("input dataset is missing or unsafe")
    return resolved


def transform(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """미래 결과와 SEC 이벤트 피처만 보존하고 중복 시점을 제거한다."""

    required = {
        "timestamp",
        "symbol",
        "label",
        *SEC_EVENT_FEATURES,
        *OUTCOME_FIELDS,
    }
    if not rows or not required.issubset(rows[0]):
        raise ValueError("SEC event dataset has an invalid schema")
    selected = {
        (row["timestamp"], row["symbol"].strip().upper()): {
            "timestamp": row["timestamp"],
            "symbol": row["symbol"].strip().upper(),
            **{name: row[name] for name in SEC_EVENT_FEATURES},
            **{name: row[name] for name in OUTCOME_FIELDS},
            "label": row["label"],
        }
        for row in rows
    }
    return sorted(selected.values(), key=lambda row: (row["timestamp"], row["symbol"]))


def main() -> int:
    """입력 CSV를 변환해 원자적으로 news.csv에 저장한다."""

    args = parse_args()
    source = safe_dataset_path(args.input)
    output_dir = safe_dataset_path(args.output_dir, directory=True)
    with source.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = transform(list(csv.DictReader(stream)))
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "news.csv"
    temporary = target.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "timestamp",
                "symbol",
                *SEC_EVENT_FEATURES,
                *OUTCOME_FIELDS,
                "label",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(target)
    print(f"news={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
