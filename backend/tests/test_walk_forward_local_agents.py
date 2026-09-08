import csv

import numpy as np
import pytest

from scripts.ai.training.walk_forward_local_agents import (
    _selective_metrics,
    dataset_feature_names,
    evaluate,
    load_rows,
    timestamp_folds,
)


def test_timestamp_folds_keep_groups_together_and_apply_purge_gap():
    unique = [f"2026-01-{index:03d}" for index in range(120)]
    timestamps = np.asarray([value for value in unique for _ in range(2)])

    folds = timestamp_folds(timestamps, splits=4, purge=5)

    assert len(folds) == 4
    for train, validation in folds:
        train_timestamps = set(timestamps[train])
        validation_timestamps = set(timestamps[validation])
        assert train_timestamps.isdisjoint(validation_timestamps)
        train_end = unique.index(max(train_timestamps))
        validation_start = unique.index(min(validation_timestamps))
        assert validation_start - train_end > 5


def test_load_rows_rejects_out_of_order_timestamps(tmp_path):
    path = tmp_path / "technical.csv"
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["timestamp", "label", "feature"])
        writer.writeheader()
        writer.writerows(
            [
                {"timestamp": "2026-01-02", "label": 0, "feature": 1.0},
                {"timestamp": "2026-01-01", "label": 1, "feature": 2.0},
            ]
        )

    with pytest.raises(ValueError, match="timestamps must be ordered"):
        load_rows(path, ("feature",))


def test_load_rows_filters_ambiguous_outcomes_without_using_them_as_features(tmp_path):
    path = tmp_path / "technical.csv"
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=["timestamp", "label", "feature", "future_excess_return"],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "timestamp": f"2026-01-{index:02d}",
                    "label": index % 2,
                    "feature": index,
                    "future_excess_return": outcome,
                }
                for index, outcome in enumerate((0.005, -0.02, 0.03), start=1)
            ]
        )

    features, labels, timestamps = load_rows(
        path,
        ("feature",),
        min_absolute_outcome=0.01,
    )

    assert features.shape == (2, 1)
    assert labels.tolist() == [0, 1]
    assert timestamps.tolist() == ["2026-01-02", "2026-01-03"]


def test_selective_metrics_report_accuracy_and_coverage():
    probabilities = np.asarray([0.9, 0.8, 0.52, 0.48, 0.2, 0.1] * 15)
    actuals = np.asarray([1, 1, 0, 1, 0, 0] * 15)

    result = _selective_metrics(probabilities, actuals, cutoff=0.8)

    assert result is not None
    assert result["samples"] == 60
    assert result["coverage"] == pytest.approx(2 / 3, abs=0.0001)
    assert result["accuracy"] == 1.0


def test_dataset_feature_names_excludes_future_outcomes(tmp_path):
    path = tmp_path / "technical.csv"
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=[
                "timestamp",
                "symbol",
                "feature",
                "future_return",
                "future_excess_return",
                "label",
            ],
        )
        writer.writeheader()

    assert dataset_feature_names(path) == ("feature",)


def test_evaluate_reports_majority_baseline_improvement():
    x = np.arange(120, dtype=float).reshape(-1, 1)
    y = np.asarray(([0] * 45 + [1] * 15) * 2)
    folds = [
        (np.arange(0, 50), np.arange(50, 80)),
        (np.arange(0, 80), np.arange(80, 120)),
    ]

    result = evaluate(x, y, folds, inverse_regularization=0.01, balanced=False)

    assert "baseline_accuracy" in result
    assert result["baseline_improvement"] == pytest.approx(
        result["accuracy"] - result["baseline_accuracy"], abs=0.0001
    )
