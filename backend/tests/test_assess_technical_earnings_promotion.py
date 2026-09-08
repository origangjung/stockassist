from copy import deepcopy

from scripts.ai.training.assess_technical_earnings_promotion import assess


def _report(*, candidate: bool) -> dict[str, object]:
    return {
        "promotion_ready": True,
        "metrics": {
            "validation_samples": 10_000,
            "mae": 0.038 if candidate else 0.04,
            "return_correlation": 0.12 if candidate else 0.1,
            "minimum_fold_mae_improvement": 0.0001,
            "subgroup:earnings_event_10d": {
                "samples": 500,
                "mae": 0.045 if candidate else 0.05,
                "zero_baseline_mae": 0.06,
                "actionable_coverage": 0.3,
                "actionable_direction_accuracy": 0.6 if candidate else 0.55,
            },
        },
        "selected_feature_sets": {"extra:earnings": 3, "base": 2},
        "folds": [{}, {}, {}, {}, {}],
    }


def test_earnings_assessment_accepts_only_consistent_incremental_value():
    report = assess(_report(candidate=False), _report(candidate=True))

    assert report["promotion_ready"] is True
    assert report["automatic_promotion"] is False
    assert report["reasons"] == []
    assert report["comparison"]["event_mae_delta"] == 0.005


def test_earnings_assessment_rejects_event_and_fold_regressions():
    base = _report(candidate=False)
    candidate = deepcopy(_report(candidate=True))
    candidate["metrics"]["minimum_fold_mae_improvement"] = -0.001
    candidate["metrics"]["subgroup:earnings_event_10d"]["mae"] = 0.06
    candidate["metrics"]["subgroup:earnings_event_10d"][
        "actionable_direction_accuracy"
    ] = 0.5
    candidate["selected_feature_sets"] = {"extra:earnings": 1, "base": 4}

    report = assess(base, candidate)

    assert report["promotion_ready"] is False
    assert "unstable_outer_fold" in report["reasons"]
    assert "event_mae_not_improved" in report["reasons"]
    assert "event_direction_accuracy_not_improved" in report["reasons"]
    assert "earnings_features_not_selected_consistently" in report["reasons"]
