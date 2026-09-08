"""기술 AI 데이터를 동일 날짜 미래 초과수익 순위 타깃으로 다시 라벨링한다."""

import argparse
import csv
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.cross_section_features import (  # noqa: E402
    TARGET_RANK_COLUMN,
    relabel_cross_section_outcomes,
)


def parse_args() -> argparse.Namespace:
    """원본과 후보 CSV 경로, 꼬리 표본 비율을 읽는다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tail-fraction", type=float, default=0.25)
    parser.add_argument("--minimum-symbols", type=int, default=5)
    parser.add_argument("--outcome-column", default="future_excess_return")
    return parser.parse_args()


def _safe_output(path: Path) -> Path:
    """생성 데이터가 Git 제외 대상인 datasets 디렉터리 안에만 기록되게 한다."""

    root = (ROOT / "datasets").resolve()
    resolved = path.expanduser().resolve()
    if resolved.suffix.casefold() != ".csv" or not resolved.is_relative_to(root):
        raise ValueError("output must be a CSV inside datasets")
    if resolved == root / "local-ai" / "technical.csv":
        raise ValueError("the active source dataset cannot be overwritten")
    return resolved


def main() -> int:
    """원본을 읽어 중립 표본을 제외한 횡단면 후보 데이터를 원자적으로 쓴다."""

    args = parse_args()
    source_path = args.input.expanduser().resolve()
    if not source_path.is_file() or source_path.is_symlink():
        raise ValueError("input dataset is missing or unsafe")
    with source_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        rows = list(reader)
        input_fields = reader.fieldnames or []
    required = {"timestamp", "symbol", "label", args.outcome_column}
    if not rows or not required.issubset(input_fields):
        raise ValueError("input dataset is empty or missing required columns")

    relabeled = relabel_cross_section_outcomes(
        rows,
        outcome_column=args.outcome_column,
        tail_fraction=args.tail_fraction,
        minimum_symbols=args.minimum_symbols,
    )
    if not relabeled:
        raise ValueError("no timestamp has enough comparable symbols")

    output_path = _safe_output(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        name for name in input_fields if name not in {"label", "label_basis"}
    ]
    if TARGET_RANK_COLUMN not in fieldnames:
        fieldnames.append(TARGET_RANK_COLUMN)
    fieldnames.extend(("label_basis", "label"))
    temporary = output_path.with_suffix(".csv.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(relabeled)
        temporary.replace(output_path)
    finally:
        temporary.unlink(missing_ok=True)

    positives = sum(int(row["label"]) for row in relabeled)
    print(
        f"rows={len(relabeled)} timestamps="
        f"{len({str(row['timestamp']) for row in relabeled})} "
        f"positive_rate={positives / len(relabeled):.4f} output={output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
