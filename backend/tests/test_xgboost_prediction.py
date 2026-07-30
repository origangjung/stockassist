from dataclasses import replace

import pytest

pytestmark = pytest.mark.ml
pytest.importorskip("sklearn")
pytest.importorskip("xgboost")

from app.adapters.broker import BrokerAdapter  # noqa: E402
from app.prediction.artifacts import ModelArtifactStore  # noqa: E402
from app.prediction.engine import XGBoostPredictionEngine  # noqa: E402
from app.providers.mock import MockProvider  # noqa: E402
from app.repositories.memory import InMemoryPredictionRepository  # noqa: E402
from app.services.model_registry import ModelRegistryService  # noqa: E402
from app.services.prediction import PredictionService  # noqa: E402


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


def test_promoted_xgboost_artifact_is_used_for_runtime_inference(tmp_path):
    store = ModelArtifactStore(tmp_path / "models")
    repository = InMemoryPredictionRepository()
    candles = MockProvider().get_candles("005930", 180)
    engine = XGBoostPredictionEngine(artifact_store=store)
    prediction = engine.predict("005930", candles, horizon_days=5)
    repository.save(prediction, algorithm="xgboost")

    promoted = ModelRegistryService(repository, store).promote(prediction.model_version)
    runtime = engine.predict("005930", candles, horizon_days=5)

    assert promoted["runtime_activation"] is True
    assert runtime.model_version == prediction.model_version
    assert runtime.validation_metrics == prediction.validation_metrics
