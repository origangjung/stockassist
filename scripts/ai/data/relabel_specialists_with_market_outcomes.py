"""Align every specialist label to the same point-in-time market outcome."""

import argparse
from bisect import bisect_right
import csv
from datetime import date
import json
from pathlib import Path


OUTCOME_FIELDS = (
    "future_return",
    "benchmark_future_return",
    "future_excess_return",
    "horizon_days",
)
OBSOLETE_FIELDS = {"future_tone_change"}


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--market-data-dir", type=Path, required=True)
    parser.add_argument("--market-outcomes", type=Path)
    parser.add_argument("--source-data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--agent",
        action="append",
        choices=("technical", "financial", "news", "investor_flow", "risk"),
        required=True,
    )
    return parser.parse_args()


def _key(row: dict[str, str]) -> tuple[str, str]:
    """`_key`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return str(row["timestamp"])[:10], str(row["symbol"]).strip().upper()


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """`_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        return list(reader.fieldnames or []), list(reader)


def _outcomes(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    """`_outcomes`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    _, rows = _read(path)
    required = {
        "timestamp",
        "symbol",
        "future_return",
        "benchmark_future_return",
        "future_excess_return",
    }
    if not rows or not required.issubset(rows[0]):
        raise ValueError("technical.csv does not contain market outcome fields")
    for row in rows:
        row.setdefault("horizon_days", "5")
    result = {_key(row): row for row in rows}
    if len(result) != len(rows):
        raise ValueError("technical.csv contains duplicate outcome keys")
    return result


def _outcome_index(
    outcomes: dict[tuple[str, str], dict[str, str]],
) -> dict[str, tuple[list[date], list[dict[str, str]]]]:
    """`_outcome_index`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    grouped: dict[str, list[dict[str, str]]] = {}
    for (_, symbol), row in outcomes.items():
        grouped.setdefault(symbol, []).append(row)
    result = {}
    for symbol, rows in grouped.items():
        rows.sort(key=lambda row: str(row["timestamp"]))
        result[symbol] = (
            [date.fromisoformat(str(row["timestamp"])[:10]) for row in rows],
            rows,
        )
    return result


def _next_outcome(
    index: dict[str, tuple[list[date], list[dict[str, str]]]],
    row: dict[str, str],
) -> dict[str, str] | None:
    """`_next_outcome`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    symbol = str(row["symbol"]).strip().upper()
    values = index.get(symbol)
    if values is None:
        return None
    dates, rows = values
    source_date = date.fromisoformat(str(row["timestamp"])[:10])
    position = bisect_right(dates, source_date)
    if position >= len(rows) or (dates[position] - source_date).days > 7:
        return None
    return rows[position]


def relabel(
    agent: str,
    source_path: Path,
    target_path: Path,
    outcomes: dict[tuple[str, str], dict[str, str]],
    outcome_index: dict[str, tuple[list[date], list[dict[str, str]]]],
) -> dict[str, int | float | str]:
    """`relabel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    original_fields, source_rows = _read(source_path)
    if not source_rows or not {"timestamp", "symbol", "label"}.issubset(original_fields):
        raise ValueError(f"{source_path.name} has an invalid schema")
    rows = []
    for source_row in source_rows:
        outcome = (
            _next_outcome(outcome_index, source_row)
            if agent == "financial"
            else outcomes.get(_key(source_row))
        )
        if outcome is None:
            continue
        excess_return = float(outcome["future_excess_return"])
        label = int(excess_return > 0)
        values = {
            name: value
            for name, value in source_row.items()
            if name not in {"label", *OUTCOME_FIELDS, *OBSOLETE_FIELDS}
        }
        values.update(
            {
                name: outcome.get(name, "5") if name == "horizon_days" else outcome[name]
                for name in OUTCOME_FIELDS
            }
        )
        if agent == "financial":
            values["outcome_start_timestamp"] = str(outcome["timestamp"])
        values["label"] = str(label)
        rows.append(values)
    rows.sort(key=lambda row: (str(row["timestamp"]), str(row["symbol"])))
    base_fields = [
        name
        for name in original_fields
        if name not in {"label", *OUTCOME_FIELDS, *OBSOLETE_FIELDS}
    ]
    alignment_fields = ["outcome_start_timestamp"] if agent == "financial" else []
    fieldnames = [*base_fields, *OUTCOME_FIELDS, *alignment_fields, "label"]
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = target_path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(target_path)
    return {
        "agent": agent,
        "source_rows": len(source_rows),
        "matched_rows": len(rows),
        "coverage": round(len(rows) / len(source_rows), 4),
        "positive_rate": round(
            sum(int(row["label"]) for row in rows) / len(rows), 4
        )
        if rows
        else 0.0,
    }


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    outcomes = _outcomes(
        args.market_outcomes or args.market_data_dir / "technical.csv"
    )
    outcome_index = _outcome_index(outcomes)
    reports = [
        relabel(
            agent,
            args.source_data_dir / f"{agent}.csv",
            args.output_dir / f"{agent}.csv",
            outcomes,
            outcome_index,
        )
        for agent in dict.fromkeys(args.agent)
    ]
    print(json.dumps(reports, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
