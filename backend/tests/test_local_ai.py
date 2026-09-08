import numpy as np
import json
import pytest

from app.local_ai.features import (
    ETF_MODEL_FEATURES,
    FEATURES,
    SYNTHESIS_FEATURES,
)
from app.local_ai.macro_features import MACRO_FEATURES
from app.local_ai.model import LocalLogisticModel
from app.local_ai.quality import MINIMUM_VALIDATION_SAMPLES
from app.local_ai.runtime import AGENTS, LocalAnalysisRuntime, _directional_signal
from scripts.ai.training.evaluate_rule_diagnostic import save_policy


def _dataset(width: int, rows: int = 100) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(42 + width)
    features = rng.normal(size=(rows, width))
    labels = (features[:, 0] + features[:, -1] * 0.25 > 0).astype(np.int8)
    return features, labels


def _save_quality_fixture(model: LocalLogisticModel, path) -> None:
    model.artifact.metrics.update(
        {
            "accuracy": 0.75,
            "baseline_accuracy": 0.55,
            "baseline_improvement": 0.20,
            "balanced_accuracy": 0.72,
            "brier_score": 0.18,
            "calibration_error": 0.05,
            "roc_auc": 0.78,
            "positive_rate": 0.55,
            "validation_samples": float(
                MINIMUM_VALIDATION_SAMPLES[model.artifact.agent]
            ),
        }
    )
    model.save(path)


def _save_diagnostic_policy(path, *, approved: bool = True) -> None:
    save_policy(
        path / "diagnostic-policy.json",
        {
            "schema_version": 1,
            "version": "rule-based-diagnostic-v1",
            "approved": approved,
            "specialists": ["investor_flow", "risk"],
            "metrics": {
                "accuracy": 0.60,
                "balanced_accuracy": 0.58,
                "baseline_improvement": 0.04,
                "minimum_fold_balanced_accuracy": 0.53,
            },
            "evaluated_at": "2026-08-13T00:00:00+00:00",
        },
    )


def test_directly_trained_model_round_trips_without_pickle(tmp_path):
    features, labels = _dataset(len(FEATURES["technical"]))
    model = LocalLogisticModel.train("technical", FEATURES["technical"], features, labels)
    path = tmp_path / "technical.json"
    model.save(path)

    loaded = LocalLogisticModel.load(path, expected_agent="technical")
    values = dict(zip(FEATURES["technical"], features[-1], strict=True))

    assert loaded.artifact.model_version.startswith("local-technical-")
    assert 0 <= loaded.predict_probability(values) <= 1
    assert loaded.artifact.metrics["validation_samples"] == 20
    assert loaded.artifact.metrics["baseline_accuracy"] >= 0.5
    assert "baseline_improvement" in loaded.artifact.metrics
    assert 0 <= loaded.artifact.metrics["roc_auc"] <= 1
    assert 0 <= loaded.artifact.metrics["calibration_error"] <= 1
    assert len(loaded.artifact.content_sha256) == 64


def test_local_model_rejects_artifact_tampering(tmp_path):
    features, labels = _dataset(len(FEATURES["technical"]))
    path = tmp_path / "technical.json"
    LocalLogisticModel.train(
        "technical", FEATURES["technical"], features, labels
    ).save(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["intercept"] += 10
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError):
        LocalLogisticModel.load(path, expected_agent="technical")


def test_local_model_rejects_non_finite_inference_features(tmp_path):
    features, labels = _dataset(len(FEATURES["technical"]))
    model = LocalLogisticModel.train(
        "technical", FEATURES["technical"], features, labels
    )
    values = dict(zip(FEATURES["technical"], features[-1], strict=True))
    values[FEATURES["technical"][0]] = float("nan")

    with pytest.raises(ValueError, match="non-finite"):
        model.predict_probability(values)


@pytest.mark.parametrize("payload", [[], {"content_sha256": "0" * 64}])
def test_local_model_rejects_malformed_json_shapes(tmp_path, payload):
    path = tmp_path / "technical.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError):
        LocalLogisticModel.load(path, expected_agent="technical")


def test_sklearn_trainer_exports_the_same_safe_json_runtime(tmp_path):
    features, labels = _dataset(len(FEATURES["risk"]))
    model = LocalLogisticModel.train_sklearn(
        "risk", FEATURES["risk"], features, labels
    )
    path = tmp_path / "risk.json"
    model.save(path)

    loaded = LocalLogisticModel.load(path, expected_agent="risk")
    values = dict(zip(FEATURES["risk"], features[-1], strict=True))

    assert loaded.artifact.model_version.startswith("local-risk-")
    assert 0 <= loaded.predict_probability(values) <= 1


def test_sklearn_trainer_supports_bounded_positive_class_weight():
    features, labels = _dataset(len(FEATURES["risk"]))

    model = LocalLogisticModel.train_sklearn(
        "risk",
        FEATURES["risk"],
        features,
        labels,
        positive_class_weight=2.0,
    )

    assert model.artifact.metrics["validation_samples"] == 20
    with pytest.raises(ValueError, match="exclusive"):
        LocalLogisticModel.train_sklearn(
            "risk",
            FEATURES["risk"],
            features,
            labels,
            class_weight_balanced=True,
            positive_class_weight=2.0,
        )


def test_sklearn_trainer_can_refit_full_data_after_holdout_metrics():
    features = np.asarray([[float(index), float(index % 3)] for index in range(100)])
    labels = np.asarray([index % 2 for index in range(100)])

    model = LocalLogisticModel.train_sklearn(
        "technical",
        ("return_5d", "return_20d"),
        features,
        labels,
        validation_start=80,
        refit_full_data=True,
    )

    assert model.artifact.training_samples == 100
    assert model.artifact.metrics["validation_samples"] == 20
    assert model.artifact.means[0] == pytest.approx(49.5)


def test_runtime_runs_all_five_specialist_models(tmp_path):
    for agent in AGENTS:
        features, labels = _dataset(len(FEATURES[agent]))
        _save_quality_fixture(
            LocalLogisticModel.train(agent, FEATURES[agent], features, labels),
            tmp_path / f"{agent}.json",
        )

    facts = {
        "local_news_features": {
            "article_count_3d": 2.1,
            "positive_ratio": 0.6,
            "negative_ratio": 0.4,
            "sentiment_balance": 0.2,
            "source_diversity": 0.8,
            "average_title_length": 0.72,
        },
        "local_financial_features": {
            "revenue_growth_yoy": 0.12,
            "net_income_growth_yoy": 0.18,
            "net_margin": 0.24,
            "debt_to_assets": 0.42,
            "equity_to_assets": 0.58,
            "asset_growth_yoy": 0.08,
        },
        "local_flow_features": {
            "short_volume_ratio": 0.48,
            "short_exempt_ratio": 0.02,
            "short_ratio_5d": 0.46,
            "short_ratio_20d": 0.44,
            "short_ratio_change_5d": 0.02,
            "reported_volume_ratio_20d": 1.1,
        },
        "local_market_features": {
            "return_1d": 0.01,
            "return_5d": 0.03,
            "sma_5_gap": 0.01,
            "sma_20_gap": 0.04,
            "volatility_20": 0.02,
            "volume_ratio": 1.2,
            "rsi_14": 0.6,
            "risk_volatility_20": 0.02,
            "risk_drawdown_20": -0.05,
            "risk_downside_deviation_20": 0.01,
            "risk_range_width_20": 0.12,
            "risk_volume_ratio": 1.2,
            "risk_market_volatility_20": 0.015,
            "risk_relative_volatility_20": 0.005,
        },
        "local_macro_features": {
            "vix_level": 0.18,
            "treasury_10y": 0.043,
            "yield_curve_10y_2y": 0.004,
            "fed_funds_rate": 0.035,
            "broad_dollar_change_20d": 0.01,
        },
        "prediction": {"rise_probability": 0.62},
        "score": {"coverage_ratio": 0.8},
        "warnings": [{"warning_type": "volatility"}],
        "chart_patterns": {"patterns": [{"name": "hammer"}]},
        "support_resistance": {"support": 90, "resistance": 110},
        "investor_flow": {"foreign_institution_net_quantity": 1200},
        "agent_findings": {
            "technical": {"value": {"score": 0.72}},
            "financial": {"value": {"score": 0.58}},
            "news": {"value": {"score": 0.61}},
            "disclosure": {"value": {"score": 0.55}},
        },
    }
    results = LocalAnalysisRuntime(tmp_path).analyze(facts)

    assert set(results) == set(AGENTS)
    assert all(result["status"] == "available" for result in results.values())
    assert all(0 <= result["probability"] <= 1 for result in results.values())
    assert all(
        any(item.startswith("validation_roc_auc=") for item in result["evidence"])
        for result in results.values()
    )


def test_runtime_routes_etfs_to_dedicated_market_models(tmp_path):
    for model_name in ("etf_technical", "etf_risk"):
        names = ETF_MODEL_FEATURES[model_name]
        features, labels = _dataset(len(names))
        _save_quality_fixture(
            LocalLogisticModel.train(model_name, names, features, labels),
            tmp_path / f"{model_name}.json",
        )
    facts = {
        "stock": {"name": "SPDR S&P 500 ETF Trust"},
        "local_market_features": {
            "return_1d": 0.01,
            "return_5d": 0.03,
            "sma_5_gap": 0.01,
            "sma_20_gap": 0.04,
            "volatility_20": 0.02,
            "volume_ratio": 1.2,
            "rsi_14": 0.6,
            "market_return_5d": 0.02,
            "market_sma_20_gap": 0.03,
            "relative_return_5d": 0.01,
            "relative_sma_20_gap": 0.01,
            "risk_volatility_20": 0.02,
            "risk_drawdown_20": -0.05,
            "risk_downside_deviation_20": 0.01,
            "risk_range_width_20": 0.12,
            "risk_volume_ratio": 1.2,
            "risk_market_volatility_20": 0.015,
            "risk_relative_volatility_20": 0.005,
        },
        "local_macro_features": {
            "vix_level": 0.18,
            "treasury_10y": 0.043,
            "yield_curve_10y_2y": 0.004,
            "fed_funds_rate": 0.035,
            "broad_dollar_change_20d": 0.01,
        },
    }

    results = LocalAnalysisRuntime(tmp_path).analyze(facts, symbol="SPY")

    assert results["technical"]["model_version"].startswith("local-etf_technical-")
    assert results["risk"]["model_version"].startswith("local-etf_risk-")
    assert "asset_scope=etf" in results["risk"]["evidence"]


def test_rule_synthesis_consumes_only_approved_specialist_summaries(tmp_path):
    _save_diagnostic_policy(tmp_path)
    specialist_results = {
        agent: {
            "status": "available",
            "probability": 0.45 + index * 0.04,
            "confidence": 0.6,
            "signal": "positive",
            "horizon_days": 5 + index,
        }
        for index, agent in enumerate(AGENTS)
    }

    result = LocalAnalysisRuntime(tmp_path).synthesize(specialist_results)

    assert result["status"] == "available"
    assert result["available_agents"] == 2
    assert result["probability"] is None
    assert result["diagnostic_score"] == 100
    assert result["model_version"] == "rule-based-diagnostic-v1"
    assert any("horizon_days:" in item for item in result["evidence"])


def test_rule_synthesis_uses_only_policy_specialists_and_reports_disagreement(tmp_path):
    _save_diagnostic_policy(tmp_path)
    specialist_results = {
        "technical": {"status": "quality_rejected"},
        "financial": {"status": "quality_rejected"},
        "news": {"status": "quality_rejected"},
        "investor_flow": {
            "status": "available",
            "confidence": 0.8,
            "signal": "negative",
        },
        "risk": {
            "status": "available",
            "confidence": 0.6,
            "signal": "positive",
        },
    }

    result = LocalAnalysisRuntime(tmp_path).synthesize(specialist_results)

    assert result["status"] == "available"
    assert result["available_agents"] == 2
    assert 0 < result["disagreement"] <= 1
    assert not any("included_technical=" in item for item in result["evidence"])


def test_etf_synthesis_uses_two_approved_specialists(tmp_path):
    specialist_results = {
        "technical": {
            "status": "available",
            "probability": 0.62,
            "confidence": 0.54,
            "signal": "positive",
        },
        "risk": {
            "status": "available",
            "probability": 0.31,
            "confidence": 0.42,
            "signal": "positive",
        },
        "financial": {"status": "data_unavailable"},
    }

    result = LocalAnalysisRuntime(tmp_path).synthesize(
        specialist_results,
        symbol="SPY",
        stock={"name": "SPDR S&P 500 ETF Trust"},
        macro_features={name: 0.1 for name in MACRO_FEATURES},
    )

    assert result["status"] == "available"
    assert result["available_agents"] == 2
    assert result["model_version"] == "rule-based-diagnostic-v1"
    assert "asset_scope=etf" in result["evidence"]


def test_etf_rule_synthesis_does_not_require_macro_features(tmp_path):
    specialist_results = {
        agent: {
            "status": "available",
            "probability": 0.55,
            "confidence": 0.4,
            "signal": "neutral",
        }
        for agent in ("technical", "risk")
    }

    result = LocalAnalysisRuntime(tmp_path).synthesize(
        specialist_results,
        symbol="SPY",
        stock={"name": "SPDR S&P 500 ETF Trust"},
    )

    assert result["status"] == "available"
    assert result["probability"] is None


def test_runtime_rejects_model_below_validation_quality_gate(tmp_path):
    features, labels = _dataset(len(FEATURES["news"]))
    model = LocalLogisticModel.train("news", FEATURES["news"], features, labels)
    model.artifact.metrics["accuracy"] = 0.49
    model.save(tmp_path / "news.json")

    result = LocalAnalysisRuntime(tmp_path).analyze(
        {
            "local_news_features": {
                name: 0.1 for name in FEATURES["news"]
            },
            "local_macro_features": {
                name: 0.1 for name in MACRO_FEATURES
            },
        }
    )["news"]

    assert result["status"] == "quality_rejected"
    assert result["probability"] is None
    assert result["model_version"].startswith("local-news-")


def test_rule_synthesis_ignores_obsolete_learned_synthesis_artifact(tmp_path):
    _save_diagnostic_policy(tmp_path)
    features, labels = _dataset(len(SYNTHESIS_FEATURES))
    model = LocalLogisticModel.train("synthesis", SYNTHESIS_FEATURES, features, labels)
    model.artifact.metrics["accuracy"] = 0.54
    model.save(tmp_path / "synthesis.json")
    specialist_results = {
        agent: {
            "status": "available",
            "probability": 0.55,
            "confidence": 0.4,
            "signal": "positive",
        }
        for agent in AGENTS
    }

    result = LocalAnalysisRuntime(tmp_path).synthesize(specialist_results)

    assert result["status"] == "available"
    assert result["model_version"] == "rule-based-diagnostic-v1"


def test_runtime_reports_missing_models_without_breaking_analysis(tmp_path):
    results = LocalAnalysisRuntime(tmp_path).analyze({})

    assert all(result["status"] == "model_missing" for result in results.values())
    assert (
        LocalAnalysisRuntime(tmp_path).synthesize(results)["status"]
        == "quality_rejected"
    )


def test_rule_synthesis_rejects_failed_historical_validation(tmp_path):
    _save_diagnostic_policy(tmp_path, approved=False)
    specialist_results = {
        agent: {"status": "available", "confidence": 0.8, "signal": "positive"}
        for agent in ("investor_flow", "risk")
    }

    result = LocalAnalysisRuntime(tmp_path).synthesize(specialist_results)

    assert result["status"] == "quality_rejected"
    assert result["diagnostic_score"] is None
    assert result["evidence"][0].startswith("diagnostic_validation_failed")


def test_agent_specific_signal_bands_abstain_on_weak_probabilities():
    assert _directional_signal("technical", 0.61) == "positive"
    assert _directional_signal("news", 0.61) == "neutral"
    assert _directional_signal("investor_flow", 0.70) == "neutral"
    assert _directional_signal("investor_flow", 0.73) == "negative"
    assert _directional_signal("investor_flow", 0.27) == "positive"
    assert _directional_signal("risk", 0.68) == "negative"
    assert _directional_signal("risk", 0.32) == "positive"
