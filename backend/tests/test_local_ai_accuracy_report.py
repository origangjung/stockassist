import pytest

from scripts.ai.training.report_local_ai_accuracy import quality_status, selected_models, wilson_interval


def test_wilson_interval_contains_observed_accuracy():
    low, high = wilson_interval(0.75, 100)

    assert low < 0.75 < high
    assert high - low < 0.2


def test_wilson_interval_rejects_invalid_input():
    with pytest.raises(ValueError):
        wilson_interval(1.1, 100)


def test_accuracy_report_uses_runtime_quality_thresholds():
    accepted = {
        "accuracy": 0.66,
        "baseline_accuracy": 0.64,
        "baseline_improvement": 0.02,
        "balanced_accuracy": 0.58,
        "brier_score": 0.21,
        "calibration_error": 0.06,
        "roc_auc": 0.61,
        "validation_samples": 500,
    }
    assert quality_status(
        "risk",
        accepted,
    ) == "available"
    assert quality_status(
        "technical",
        {**accepted, "accuracy": 0.56, "balanced_accuracy": 0.5},
    ) == "quality_rejected"
    assert quality_status(
        "synthesis",
        {**accepted, "accuracy": 0.54, "validation_samples": 2_000},
    ) == "quality_rejected"


def test_accuracy_report_rejects_small_or_non_improving_validation():
    metrics = {
        "accuracy": 0.75,
        "baseline_accuracy": 0.55,
        "baseline_improvement": 0.20,
        "balanced_accuracy": 0.72,
        "brier_score": 0.18,
        "calibration_error": 0.05,
        "roc_auc": 0.78,
        "validation_samples": 199,
    }

    assert quality_status("news", metrics) == "quality_rejected"
    assert quality_status(
        "news",
        {**metrics, "validation_samples": 200, "baseline_improvement": 0.0},
    ) == "quality_rejected"


def test_accuracy_report_rejects_uncalibrated_model():
    metrics = {
        "accuracy": 0.70,
        "baseline_accuracy": 0.55,
        "baseline_improvement": 0.15,
        "balanced_accuracy": 0.68,
        "brier_score": 0.19,
        "calibration_error": 0.11,
        "roc_auc": 0.75,
        "validation_samples": 500,
    }

    assert quality_status("risk", metrics) == "quality_rejected"


def test_accuracy_report_can_select_one_candidate_artifact():
    assert selected_models("financial", include_etf=False) == ("financial",)
    assert "etf_risk" in selected_models(None, include_etf=True)
