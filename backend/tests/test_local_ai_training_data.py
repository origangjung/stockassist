import csv

import pytest

from app.local_ai.features import FEATURES
from scripts.ai.training.train_local_agents import load_dataset


def _write(path, rows):
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=["timestamp", "symbol", *FEATURES["technical"], "label"],
        )
        writer.writeheader()
        writer.writerows(rows)


def _row(day, symbol="AAPL"):
    return {
        "timestamp": f"2026-01-{day:02d}",
        "symbol": symbol,
        **{name: 0.1 for name in FEATURES["technical"]},
        "label": day % 2,
    }


def test_training_loader_aligns_validation_to_timestamp_group(tmp_path):
    rows = [_row(day, symbol) for day in range(1, 31) for symbol in ("AAPL", "MSFT")]
    path = tmp_path / "technical.csv"
    _write(path, rows)

    _features, _labels, validation_start = load_dataset(
        path, FEATURES["technical"]
    )

    assert validation_start == 48


def test_training_loader_rejects_unsorted_or_duplicate_rows(tmp_path):
    unsorted = tmp_path / "unsorted.csv"
    _write(unsorted, [_row(2), _row(1)])
    with pytest.raises(ValueError, match="ordered"):
        load_dataset(unsorted, FEATURES["technical"])

    duplicate = tmp_path / "duplicate.csv"
    rows = [_row(day) for day in range(1, 31)]
    _write(duplicate, [*rows, rows[-1]])
    with pytest.raises(ValueError, match="duplicate"):
        load_dataset(duplicate, FEATURES["technical"])


def test_training_loader_can_limit_recent_timestamp_window(tmp_path):
    rows = [_row(day, symbol) for day in range(1, 31) for symbol in ("AAPL", "MSFT")]
    path = tmp_path / "technical.csv"
    _write(path, rows)

    features, labels, validation_start = load_dataset(
        path,
        FEATURES["technical"],
        max_training_timestamps=100,
    )

    # 데이터가 100일보다 짧으면 기존 전체 데이터와 시간 정렬을 그대로 유지한다.
    assert len(features) == len(labels) == 60
    assert validation_start == 48


def test_training_loader_rejects_too_short_rolling_window(tmp_path):
    path = tmp_path / "technical.csv"
    _write(path, [_row(day) for day in range(1, 31)])

    with pytest.raises(ValueError, match="at least 100"):
        load_dataset(path, FEATURES["technical"], max_training_timestamps=99)
