from dataclasses import replace

from app.database import Base, create_session_factory
from app.backtest import BacktestConfig, BacktestEngine, BuyAndHoldStrategy, CostModel
from app.pipeline.candles import DataQualityLog, QualitySeverity
from app.providers.mock import MockProvider
from app.repositories.sqlalchemy import (
    SqlAlchemyCandleRepository,
    SqlAlchemyQualityLogRepository,
    SqlAlchemyStockRepository,
)
from app.repositories.backtest import SqlAlchemyBacktestRepository
from app.repositories.score import SqlAlchemyScoreWeightRepository
from app.score import DEFAULT_WEIGHTS, ScoreWeights
from app.adapters.broker import BrokerAdapter
from app.indicators import IndicatorEngine
from app.services.backtest import BacktestService
from app.services.score import ScoreService
from app.prediction import XGBoostPredictionEngine
from app.repositories.sqlalchemy import SqlAlchemyPredictionRepository
from app.services.model_registry import ModelRegistryService
from app.score import ScoreEngine, TechnicalScoreCalculator


def test_sqlalchemy_repositories_upsert_and_read(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'repositories.db'}")
    Base.metadata.create_all(sessions.kw["bind"])
    provider = MockProvider()
    stock = provider.get_stock_info("005930")
    source = provider.get_candles("005930", 3)
    stocks = SqlAlchemyStockRepository(sessions)
    candles = SqlAlchemyCandleRepository(sessions)
    quality = SqlAlchemyQualityLogRepository(sessions)

    stocks.upsert(stock)
    candles.save_many("005930", source, interval="1d", stage="raw", aggregation_version="raw")
    candles.save_many("005930", source, interval="1d", stage="raw", aggregation_version="raw")
    quality.save_many("005930", [DataQualityLog("golden", QualitySeverity.WARNING, "test")])

    stored = candles.find("005930", interval="1d", stage="raw", limit=10)
    assert len(stored) == 3
    assert stored[-1].close == source[-1].close

    result = BacktestEngine().run(
        source, BuyAndHoldStrategy(), BacktestConfig(costs=CostModel(0, 0, 0))
    )
    run_id = SqlAlchemyBacktestRepository(sessions).save("005930", BacktestConfig(), result)
    assert len(run_id) == 36

    score_weights = SqlAlchemyScoreWeightRepository(sessions)
    score_weights.save(DEFAULT_WEIGHTS, activate=True)
    assert score_weights.get_active() == DEFAULT_WEIGHTS
    score_weights.save(
        ScoreWeights("weights-test", {**DEFAULT_WEIGHTS.weights, "technical": 0.4}), activate=True
    )
    assert score_weights.get_active().version == "weights-test"

    broker = BrokerAdapter([provider])
    backtests = SqlAlchemyBacktestRepository(sessions)
    persisted = BacktestService(broker, BacktestEngine(), backtests).run(
        symbol="005930",
        strategy_name="buy_and_hold",
        limit=30,
        fast_period=5,
        slow_period=20,
        initial_capital=1_000_000,
        commission_rate=0,
        tax_rate=0,
        slippage_rate=0,
    )
    assert persisted["persistence_status"] == "persisted"
    assert len(persisted["run_id"]) == 36
    history, total = backtests.list_runs(limit=10, offset=0, symbol="005930")
    assert total == 2
    assert history[0].symbol == "005930"
    assert history[0].engine == "vectorized"
    detail = backtests.get_run(persisted["run_id"])
    assert detail is not None
    assert detail.summary.run_id == persisted["run_id"]
    assert detail.trades
    assert backtests.get_run("missing") is None

    scored = ScoreService(
        broker,
        IndicatorEngine(),
        TechnicalScoreCalculator(),
        ScoreEngine(),
        score_weights,
    ).score("005930", 40)
    assert scored["weight_version"] == "weights-test"

    prediction_repository = SqlAlchemyPredictionRepository(sessions)
    prediction = XGBoostPredictionEngine().predict(
        "005930",
        provider.get_candles("005930", 180),
        horizon_days=5,
    )
    challenger = replace(prediction, model_version=f"{prediction.model_version}-next")
    prediction_repository.save(prediction, algorithm="xgboost")
    prediction_repository.save(challenger, algorithm="xgboost")
    registry = ModelRegistryService(prediction_repository)
    registry.promote(prediction.model_version)
    promoted = registry.promote(challenger.model_version)
    registered = registry.versions(limit=10, offset=0, symbol="005930")
    assert promoted["model"]["registry_stage"] == "champion"
    assert promoted["runtime_activation"] is False
    assert registered["total"] == 2
    assert sum(item["registry_stage"] == "champion" for item in registered["items"]) == 1
