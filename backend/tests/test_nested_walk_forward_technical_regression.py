from pathlib import Path

import numpy as np
import pytest

from scripts.ai.training.nested_walk_forward_technical_regression import (
    load_regression_rows,
    main as regression_main,
    nested_validate,
    resolve_requested_feature_sets,
    return_states,
    safe_output_path,
    save_report,
)


def test_return_states_keeps_small_returns_neutral():
    states = return_states(np.asarray([-0.02, -0.005, 0.0, 0.005, 0.02]), 0.01)

    assert states.tolist() == [-1, 0, 0, 0, 1]


def test_regression_loader_rejects_target_leakage_as_feature(tmp_path):
    path = tmp_path / "technical.csv"
    path.write_text(
        "timestamp,return_1d,return_5d,sma_5_gap,sma_20_gap,volatility_20,"
        "volume_ratio,rsi_14,future_excess_return\n"
        "2026-01-01,0.1,0.1,0.1,0.1,0.1,1,0.5,0.02\n",
        encoding="utf-8",
    )

    features, target, timestamps = load_regression_rows(path)

    assert features.shape == (1, 7)
    assert target.tolist() == [0.02]
    assert timestamps.tolist() == ["2026-01-01"]


def test_custom_feature_sets_reject_outcomes_and_resolve_indexes(tmp_path):
    path = tmp_path / "flow.csv"
    path.write_text(
        "timestamp,symbol,price_return_1d,short_volume_ratio,"
        "future_excess_return,label\n"
        "2026-01-01,A,0.1,0.4,0.02,1\n",
        encoding="utf-8",
    )

    features, groups = resolve_requested_feature_sets(
        path,
        ["price_return_1d"],
        ["short_volume_ratio"],
    )

    assert features == ("price_return_1d", "short_volume_ratio")
    assert groups == {"base": (0,), "extra:short_volume_ratio": (0, 1)}
    with pytest.raises(ValueError, match="invalid features"):
        resolve_requested_feature_sets(path, ["future_excess_return"], [])


def test_regression_dry_run_validates_schema_without_loading_rows(
    tmp_path, monkeypatch, capsys
):
    path = tmp_path / "candidate.csv"
    path.write_text(
        "timestamp,symbol,return_1d,eps_surprise_signed_log,"
        "future_excess_return,label\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "nested-regression",
            "--data",
            str(path),
            "--base-feature",
            "return_1d",
            "--candidate-extra-feature-set",
            "eps_surprise_signed_log",
            "--output",
            str(tmp_path / "report.json"),
            "--dry-run",
        ],
    )

    assert regression_main() == 0
    output = capsys.readouterr().out
    assert '"validation": "planned"' in output
    assert '"automatic_promotion": false' in output
    assert not (tmp_path / "report.json").exists()


def test_nested_regression_finds_past_only_signal():
    random = np.random.default_rng(42)
    rows = 900
    signal = random.normal(size=rows)
    x = np.column_stack(
        (signal, *(random.normal(size=rows) for _ in range(6)))
    )
    y = signal * 0.02 + random.normal(scale=0.005, size=rows)
    timestamps = np.asarray([f"2026-{index:05d}" for index in range(rows)])

    report = nested_validate(
        x,
        y,
        timestamps,
        (0.1, 1.0, 10.0),
        outer_splits=3,
        inner_splits=2,
        purge=2,
        neutral_return=0.01,
    )

    assert report["metrics"]["mae_improvement"] > 0
    assert report["metrics"]["return_correlation"] > 0.8
    assert report["metrics"]["three_state_balanced_accuracy"] > 0.7
    assert report["metrics"]["minimum_fold_mae_improvement"] > 0
    assert report["metrics"]["unique_timestamps"] == rows
    assert report["promotion_ready"] is True
    assert len(report["folds"]) == 3


def test_nested_regression_selects_feature_sets_inside_outer_training_periods():
    random = np.random.default_rng(7)
    rows = 900
    signal = random.normal(size=rows)
    noise = random.normal(size=rows)
    x = np.column_stack((noise, signal))
    y = signal * 0.03 + random.normal(scale=0.003, size=rows)
    timestamps = np.asarray([f"2026-{index:05d}" for index in range(rows)])

    report = nested_validate(
        x,
        y,
        timestamps,
        (1.0,),
        outer_splits=3,
        inner_splits=2,
        purge=2,
        feature_sets={"base": (0,), "extra:signal": (0, 1)},
    )

    assert report["selected_feature_sets"] == {"extra:signal": 3}
    assert all(
        fold["selected_feature_set"] == "extra:signal" for fold in report["folds"]
    )


def test_nested_regression_reports_a_holdout_subgroup_separately():
    random = np.random.default_rng(11)
    rows = 900
    signal = random.normal(size=rows)
    x = signal.reshape(-1, 1)
    y = signal * 0.02 + random.normal(scale=0.004, size=rows)
    subgroup = np.asarray([index % 3 == 0 for index in range(rows)], dtype=float)
    timestamps = np.asarray([f"2026-{index:05d}" for index in range(rows)])

    report = nested_validate(
        x,
        y,
        timestamps,
        (1.0,),
        outer_splits=3,
        inner_splits=2,
        purge=2,
        subgroup_values=subgroup,
        subgroup_name="event",
    )

    event = report["metrics"]["subgroup:event"]
    assert event["samples"] > 100
    assert event["mae"] < event["zero_baseline_mae"]
    assert event["actionable_direction_accuracy"] > 0.8


def test_regression_report_is_atomic_and_restricted(tmp_path, monkeypatch):
    artifact_root = tmp_path / "artifacts"
    monkeypatch.setattr(
        "scripts.ai.training.nested_walk_forward_technical_regression.ARTIFACT_ROOT",
        artifact_root.resolve(),
    )
    output = safe_output_path(artifact_root / "technical" / "validation.json")

    save_report(output, {"promotion_ready": False})

    assert output.is_file()
    assert list(output.parent.glob(".*.tmp")) == []
    with pytest.raises(ValueError, match="inside artifacts"):
        safe_output_path(Path(tmp_path) / "outside.json")
