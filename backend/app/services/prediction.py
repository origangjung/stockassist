from app.adapters.broker import BrokerAdapter
from app.prediction.contracts import PredictionEngine
from app.repositories.contracts import PredictionRepository


class PredictionService:
    def __init__(
        self,
        broker: BrokerAdapter,
        engine: PredictionEngine,
        repository: PredictionRepository | None = None,
    ) -> None:
        self._broker = broker
        self._engine = engine
        self._repository = repository

    def predict(self, symbol: str, *, horizon_days: int, limit: int) -> dict:
        symbol = symbol.strip().upper()
        batch = self._broker.candles(symbol, limit)
        result = self._engine.predict(
            symbol,
            batch.candles,
            horizon_days=horizon_days,
        )
        if self._repository is not None:
            self._repository.save(result, algorithm=self._engine.algorithm)
        return {
            **result.__dict__,
            "provider": batch.provider.name,
            "algorithm": self._engine.algorithm,
            "is_prediction": True,
            "persistence_status": "saved" if self._repository is not None else "disabled",
        }
