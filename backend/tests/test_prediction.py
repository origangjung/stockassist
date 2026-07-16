from dataclasses import replace

from app.prediction.engine import XGBoostPredictionEngine
from app.prediction.features import build_feature_dataset
from app.prediction.lightweight import LightweightPredictionEngine
from app.prediction.validation import PurgedWalkForwardSplit
from app.providers.mock import MockProvider
from app.repositories.memory import InMemoryPredictionRepository
from app.services.prediction import PredictionService
from app.services.model_registry import ModelRegistryService
from app.adapters.broker import BrokerAdapter


def test_lightweight_prediction_engine_runs_without_model_training():
    candles = MockProvider().get_candles("005930", 60)

    result = LightweightPredictionEngine().predict("005930", candles, horizon_days=5)

    assert 0 <= result.rise_probability <= 1
    assert result.model_version.startswith("light-")
    assert result.validation_status == "experimental"
    assert result.validation_metrics["folds"] == 0


def test_feature_rows_do_not_use_future_prices():
    candles = MockProvider().get_candles("005930", 100)
    dataset = build_feature_dataset(candles, horizon_days=5)
    altered = [*candles]
    altered[-1] = altered[-1].__class__(
        altered[-1].timestamp,
        altered[-1].open,
        altered[-1].high,
        altered[-1].low,
        altered[-1].close * 2,
        altered[-1].volume,
    )
    altered_dataset = build_feature_dataset(altered, horizon_days=5)

    assert (dataset.features[:-1] == altered_dataset.features[:-1]).all()
    assert (dataset.labels[:-1] == altered_dataset.labels[:-1]).all()
    assert not (dataset.prediction_features == altered_dataset.prediction_features).all()


def test_purged_walk_forward_keeps_label_horizon_out_of_train_set():
    splits = list(PurgedWalkForwardSplit(horizon_days=5, min_train_size=40, n_splits=3).split(120))

    assert len(splits) == 3
    for train, test in splits:
        assert train.max() + 5 < test.min()


def test_prediction_service_returns_probability_interval_and_version():
    repository = InMemoryPredictionRepository()
    service = PredictionService(
        BrokerAdapter([MockProvider()]), XGBoostPredictionEngine(), repository
    )

    result = service.predict("005930", horizon_days=5, limit=180)

    assert result["validation_status"] == "experimental"
    assert 0 <= result["rise_probability"] <= 1
    assert result["confidence_lower"] <= result["rise_probability"] <= result["confidence_upper"]
    assert result["model_version"].startswith("xgb-")
    assert result["persistence_status"] == "saved"
    assert len(repository.items) == 1


def test_model_version_fingerprint_is_scoped_to_symbol():
    candles = MockProvider().get_candles("005930", 180)
    engine = XGBoostPredictionEngine()

    samsung = engine.predict("005930", candles, horizon_days=5)
    synthetic_other_symbol = engine.predict("AAPL", candles, horizon_days=5)

    assert samsung.model_version != synthetic_other_symbol.model_version


def test_model_registry_promotes_one_champion_per_symbol_algorithm_and_horizon():
    repository = InMemoryPredictionRepository()
    prediction = XGBoostPredictionEngine().predict(
        "005930",
        MockProvider().get_candles("005930", 180),
        horizon_days=5,
    )
    challenger = replace(prediction, model_version=f"{prediction.model_version}-next")
    repository.save(prediction, algorithm="xgboost")
    repository.save(challenger, algorithm="xgboost")
    registry = ModelRegistryService(repository)

    first = registry.promote(prediction.model_version)
    second = registry.promote(challenger.model_version)
    listed = registry.versions(limit=10, offset=0, symbol="005930")

    assert first["model"]["registry_stage"] == "champion"
    assert second["model"]["registry_stage"] == "champion"
    assert second["runtime_activation"] is False
    assert listed["total"] == 2
    assert sum(item["registry_stage"] == "champion" for item in listed["items"]) == 1
    assert repository.get_version(prediction.model_version).registry_stage == "challenger"
