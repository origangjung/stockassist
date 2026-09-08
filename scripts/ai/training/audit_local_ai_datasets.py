"""원시 행이나 특성 값을 출력하지 않고 로컬 AI CSV 품질과 재학습 준비도를 감사한다."""

import argparse
import csv
from datetime import datetime
import json
import math
import os
from pathlib import Path
import statistics
import sys
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.features import (  # noqa: E402
    ETF_MODEL_FEATURES,
    ETF_SYNTHESIS_FEATURES,
    FEATURES,
    SYNTHESIS_FEATURES,
)
from app.local_ai.quality import MINIMUM_VALIDATION_SAMPLES  # noqa: E402


MODEL_FEATURES = {
    **FEATURES,
    "synthesis": SYNTHESIS_FEATURES,
    **ETF_MODEL_FEATURES,
    "etf_synthesis": ETF_SYNTHESIS_FEATURES,
}
NON_FEATURE_COLUMNS = {
    "timestamp",
    "symbol",
    "label",
    "future_return",
    "close_price",
    "benchmark_future_return",
    "future_excess_return",
    "future_max_drawdown",
    "future_tone_change",
    "outcome_start_timestamp",
    "accession",
    "feature_timestamp",
    "valuation_filed",
    "valuation_price_timestamp",
    "pit_per",
    "pit_pbr",
    "pit_psr",
    "pit_roe",
    "sector",
    "label_basis",
    "sector_neutral_future_return",
    "sample_weight",
    "horizon_days",
}


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--agent", action="append", choices=sorted(MODEL_FEATURES))
    parser.add_argument("--all-safe-features", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        help="데이터 디렉터리 내부에 저장할 JSON 감사 보고서 경로",
    )
    return parser.parse_args()


def _validation_start(timestamps: list[datetime]) -> int:
    """같은 시각 그룹이 학습과 검증 양쪽에 섞이지 않도록 80% 경계를 앞으로 맞춘다."""

    if len(timestamps) < 2:
        return len(timestamps)
    desired = min(int(len(timestamps) * 0.8), len(timestamps) - 1)
    boundary = timestamps[desired]
    while desired > 0 and timestamps[desired - 1] == boundary:
        desired -= 1
    return desired


def _training_readiness(
    *,
    structural_status: str,
    holdout_labels: list[int],
    holdout_timestamps: list[datetime],
    minimum_validation_samples: int,
) -> tuple[str, list[str]]:
    """구조 검사를 통과한 데이터가 후보 재학습에 충분한지 보수적으로 판정한다."""

    reasons: list[str] = []
    if structural_status != "ok":
        reasons.append("structural_quality_failed")
    if len(holdout_labels) < minimum_validation_samples:
        reasons.append(f"validation_rows<{minimum_validation_samples}")
    if len(set(holdout_timestamps)) < 10:
        reasons.append("validation_timestamp_groups<10")
    if len(set(holdout_labels)) < 2:
        reasons.append("validation_labels_need_both_classes")
    if holdout_labels:
        positive_rate = sum(holdout_labels) / len(holdout_labels)
        if not 0.1 <= positive_rate <= 0.9:
            reasons.append("validation_positive_rate_outside_0.10_0.90")
    return ("collect_more_data", reasons) if reasons else ("ready_for_candidate_training", [])


def audit(
    path: Path,
    features: tuple[str, ...],
    *,
    minimum_validation_samples: int = 200,
) -> dict[str, object]:
    """한 CSV의 무결성과 시간순 후보 재학습 준비도를 요약한다."""

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    required = {"timestamp", "symbol", "label", *features}
    columns = set(rows[0]) if rows else set()
    missing_columns = sorted(required - columns)
    keys: list[tuple[str, str]] = []
    timestamps: list[datetime] = []
    symbols: dict[str, int] = {}
    labels: list[int] = []
    invalid_numeric_values = 0
    missing_values = 0
    for row in rows:
        keys.append((str(row.get("timestamp", "")), str(row.get("symbol", ""))))
        try:
            timestamps.append(datetime.fromisoformat(str(row["timestamp"]).replace("Z", "+00:00")))
            labels.append(int(row["label"]))
        except (KeyError, TypeError, ValueError):
            missing_values += 1
        symbol = str(row.get("symbol", "")).strip().upper()
        symbols[symbol] = symbols.get(symbol, 0) + 1
        for name in features:
            raw = row.get(name)
            if raw in {None, ""}:
                missing_values += 1
                continue
            try:
                if not math.isfinite(float(raw)):
                    invalid_numeric_values += 1
            except (TypeError, ValueError):
                invalid_numeric_values += 1
    ordered = [value.isoformat() for value in timestamps]
    validation_start = _validation_start(timestamps)
    holdout_labels = labels[validation_start:]
    holdout_timestamps = timestamps[validation_start:]
    counts = list(symbols.values())
    today_kst = datetime.now(ZoneInfo("Asia/Seoul")).date()
    future_timestamps = sum(value.date() > today_kst for value in timestamps)
    duplicate_keys = len(keys) - len(set(keys))
    valid_labels = set(labels).issubset({0, 1}) and len(set(labels)) == 2
    status = (
        "ok"
        if rows
        and not missing_columns
        and not missing_values
        and not invalid_numeric_values
        and not duplicate_keys
        and not future_timestamps
        and ordered == sorted(ordered)
        and valid_labels
        else "failed"
    )
    readiness, readiness_reasons = _training_readiness(
        structural_status=status,
        holdout_labels=holdout_labels,
        holdout_timestamps=holdout_timestamps,
        minimum_validation_samples=minimum_validation_samples,
    )
    return {
        "status": status,
        "training_readiness": readiness,
        "readiness_reasons": readiness_reasons,
        "rows": len(rows),
        "symbols": len(symbols),
        "period_start": min(ordered)[:10] if ordered else None,
        "period_end": max(ordered)[:10] if ordered else None,
        "duplicate_keys": duplicate_keys,
        "missing_columns": missing_columns,
        "missing_values": missing_values,
        "invalid_numeric_values": invalid_numeric_values,
        "future_timestamps": future_timestamps,
        "timestamp_ordered": ordered == sorted(ordered),
        "positive_rate": round(sum(labels) / len(labels), 4) if labels else None,
        "validation_rows": len(holdout_labels),
        "minimum_validation_rows": minimum_validation_samples,
        "validation_timestamp_groups": len(set(holdout_timestamps)),
        "holdout_positive_rate": round(sum(holdout_labels) / len(holdout_labels), 4)
        if holdout_labels
        else None,
        "minimum_rows_per_symbol": min(counts) if counts else 0,
        "median_rows_per_symbol": statistics.median(counts) if counts else 0,
        "maximum_symbol_share": round(max(counts) / len(rows), 4) if rows else None,
    }


def safe_report_path(data_dir: Path, output: Path) -> Path:
    """감사 보고서가 Git 제외 데이터 디렉터리 밖에 기록되지 않게 제한한다."""

    root = data_dir.expanduser().resolve()
    path = output.expanduser().resolve()
    if path.suffix.casefold() != ".json" or not path.is_relative_to(root):
        raise ValueError("audit output must be a JSON file inside the data directory")
    return path


def save_report(path: Path, report: dict[str, object]) -> None:
    """감사 보고서를 배타적 임시 파일에 쓴 뒤 원자적으로 교체한다."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor: int | None = None
    try:
        descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = None
            json.dump(report, stream, ensure_ascii=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    selected = args.agent or [
        name for name in MODEL_FEATURES if (args.data_dir / f"{name}.csv").is_file()
    ]
    report = {}
    for agent in selected:
        path = args.data_dir / f"{agent}.csv"
        features = MODEL_FEATURES[agent]
        if args.all_safe_features:
            with path.open("r", encoding="utf-8-sig", newline="") as source:
                fieldnames = csv.DictReader(source).fieldnames or []
            features = tuple(
                name for name in fieldnames if name not in NON_FEATURE_COLUMNS
            )
        report[agent] = audit(
            path,
            features,
            minimum_validation_samples=MINIMUM_VALIDATION_SAMPLES[agent],
        )
        report[agent]["audited_feature_count"] = len(features)
    if args.output:
        save_report(safe_report_path(args.data_dir, args.output), report)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 1 if not report or any(item["status"] != "ok" for item in report.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
