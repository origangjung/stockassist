from pathlib import Path

import numpy as np
import pytest

from scripts.ai.training.nested_walk_forward_local_agent import (
    _correct_balanced_probabilities,
    _limit_training_window,
    _select_threshold,
    candidate_settings,
    nested_validate,
    resolve_features,
    resolve_feature_sets,
    safe_output_path,
    save_report,
)
from scripts.ai.training.walk_forward_local_agents import load_rows
from scripts.ai.training.walk_forward_local_agents import dataset_feature_names


def test_training_window_keeps_only_latest_timestamps():
    timestamps = np.asarray([f"2026-{index:04d}" for index in range(300)])
    train = np.arange(250)

    limited = _limit_training_window(train, timestamps, 100)

    assert limited.tolist() == list(range(150, 250))


def test_nested_validation_rejects_invalid_fixed_threshold():
    with pytest.raises(ValueError, match="fixed decision threshold"):
        nested_validate(
            "risk",
            np.ones((300, 1)),
            np.asarray([index % 2 for index in range(300)]),
            np.asarray([f"2026-{index:04d}" for index in range(300)]),
            candidate_settings([0.1]),
            outer_splits=3,
            inner_splits=2,
            purge=2,
            fixed_decision_threshold=1.0,
        )


def test_candidate_settings_can_lock_class_weight_mode():
    unweighted = candidate_settings([0.01, 0.1], "unweighted")
    balanced = candidate_settings([0.01], "balanced")

    assert [setting.key for setting in unweighted] == [
        "c=0.01,unweighted",
        "c=0.1,unweighted",
    ]
    assert [setting.key for setting in balanced] == ["c=0.01,balanced"]
    with pytest.raises(ValueError, match="class weight mode"):
        candidate_settings([0.1], "invalid")


def test_outcome_filter_keeps_only_decisive_rows(tmp_path):
    path = tmp_path / "technical.csv"
    path.write_text(
        "timestamp,return_1d,future_excess_return,label\n"
        "2026-01-01,0.1,0.001,1\n"
        "2026-01-02,0.2,-0.010,0\n"
        "2026-01-03,0.3,0.020,1\n",
        encoding="utf-8",
    )

    features, labels, timestamps = load_rows(
        path,
        ("return_1d",),
        min_absolute_outcome=0.005,
    )

    assert features[:, 0].tolist() == [0.2, 0.3]
    assert labels.tolist() == [0, 1]
    assert timestamps.tolist() == ["2026-01-02", "2026-01-03"]


def test_balanced_probability_correction_restores_training_prior():
    labels = np.asarray([0] * 80 + [1] * 20, dtype=np.int8)
    corrected = _correct_balanced_probabilities(
        np.asarray([0.5, 0.5]),
        labels,
    )

    assert corrected.tolist() == pytest.approx([0.2, 0.2])


def test_threshold_selection_uses_validation_signal_instead_of_fixed_half():
    actual = np.asarray([0, 0, 1, 1], dtype=np.int8)
    probability = np.asarray([0.10, 0.20, 0.30, 0.40])

    threshold = _select_threshold(actual, probability)

    assert 0.20 < threshold <= 0.30


def test_threshold_selection_prefers_baseline_beating_balanced_option():
    actual = np.asarray([0] * 8 + [1] * 2, dtype=np.int8)
    probability = np.asarray(
        [0.05, 0.08, 0.1, 0.12, 0.15, 0.2, 0.35, 0.6, 0.55, 0.9]
    )

    threshold = _select_threshold(actual, probability)
    predictions = probability >= threshold
    accuracy = float(np.mean(predictions == actual))
    true_positive_rate = float(np.mean(predictions[actual == 1]))
    true_negative_rate = float(np.mean(~predictions[actual == 0]))

    assert accuracy > 0.8
    assert (true_positive_rate + true_negative_rate) / 2 > 0.5


def test_nested_validation_accepts_only_explicit_safe_extra_features(tmp_path):
    path = tmp_path / "financial.csv"
    path.write_text(
        "timestamp,symbol,revenue_growth_yoy,net_income_growth_yoy,net_margin,"
        "debt_to_assets,equity_to_assets,asset_growth_yoy,pit_roe_signed_log,pit_roe,label\n"
        "2025-01-01,AAPL,1,1,1,1,1,1,0.1,0.2,1\n",
        encoding="utf-8",
    )

    features = resolve_features(path, "financial", ["pit_roe_signed_log"])

    assert features[-1] == "pit_roe_signed_log"
    with pytest.raises(ValueError, match="invalid extra features"):
        resolve_features(path, "financial", ["pit_roe"])


def test_nested_validation_selects_settings_inside_each_outer_training_period():
    random = np.random.default_rng(42)
    rows = 600
    signal = random.normal(size=rows)
    x = np.column_stack((signal, random.normal(size=rows)))
    y = (signal + random.normal(scale=0.8, size=rows) > 0).astype(np.int8)
    timestamps = np.asarray([f"2020-01-{index + 1:04d}" for index in range(rows)])

    report = nested_validate(
        "financial",
        x,
        y,
        timestamps,
        candidate_settings([0.05, 0.5]),
        outer_splits=3,
        inner_splits=2,
        purge=2,
        sample_weights=np.asarray(
            [1.0 / (1 + index % 4) for index in range(rows)], dtype=float
        ),
        feature_sets={"signal_only": (0,), "all": (0, 1)},
    )

    assert report["metrics"]["validation_samples"] >= 200
    assert report["metrics"]["roc_auc"] > 0.7
    assert "fold_positive_rate_range" in report["metrics"]
    assert "minimum_fold_baseline_improvement" in report["metrics"]
    assert report["metrics"]["validation_weight"] > 0
    assert len(report["folds"]) == 3
    assert sum(report["selected_settings"].values()) == 3
    assert sum(report["selected_feature_sets"].values()) == 3


def test_nested_validation_selects_feature_groups_only_inside_training_folds(tmp_path):
    path = tmp_path / "financial.csv"
    path.write_text(
        "timestamp,symbol,revenue_growth_yoy,net_income_growth_yoy,net_margin,"
        "debt_to_assets,equity_to_assets,asset_growth_yoy,pit_roe_signed_log,pit_pbr_signed_log,label\n"
        "2025-01-01,AAPL,1,1,1,1,1,1,0.1,0.2,1\n",
        encoding="utf-8",
    )
    features, groups = resolve_feature_sets(
        path,
        "financial",
        [],
        ["pit_roe_signed_log", "pit_roe_signed_log,pit_pbr_signed_log"],
    )

    assert set(groups) == {
        "base",
        "extra:pit_roe_signed_log",
        "extra:pit_roe_signed_log,pit_pbr_signed_log",
    }
    assert features[-2:] == ("pit_roe_signed_log", "pit_pbr_signed_log")


def test_nested_validation_report_is_atomic_and_restricted_to_artifacts(tmp_path, monkeypatch):
    artifact_root = tmp_path / "artifacts"
    monkeypatch.setattr(
        "scripts.ai.training.nested_walk_forward_local_agent.ARTIFACT_ROOT",
        artifact_root.resolve(),
    )
    output = safe_output_path(artifact_root / "candidate" / "nested.json")

    save_report(output, {"promotion_ready": False})

    assert output.is_file()
    assert list(output.parent.glob(".*.tmp")) == []
    with pytest.raises(ValueError, match="inside artifacts"):
        safe_output_path(Path(tmp_path) / "outside.json")


def test_cross_section_target_rank_is_never_used_as_a_training_feature(tmp_path):
    path = tmp_path / "technical.csv"
    path.write_text(
        "timestamp,symbol,return_1d,future_excess_return,"
        "future_excess_return_cross_section_rank,label\n"
        "2026-01-01,A,0.1,0.02,1.0,1\n",
        encoding="utf-8",
    )

    assert "future_excess_return_cross_section_rank" not in dataset_feature_names(path)
