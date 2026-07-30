from app.adapters.broker import BrokerAdapter
from app.indicators import IndicatorEngine
from app.pipeline.candles import CandlePipeline


class TechnicalAnalysisService:
    def __init__(self, broker: BrokerAdapter, engine: IndicatorEngine):
        self._broker = broker
        self._engine = engine
        self._pipeline = CandlePipeline()

    def indicators(self, symbol: str, limit: int) -> dict:
        batch = self._broker.candles(symbol, limit)
        cleaned = self._pipeline.process(batch.candles).cleaned_candles
        return {
            "symbol": symbol,
            "provider": batch.provider.name,
            "engine_version": self._engine.version,
            "validation_status": self._engine.status,
            "indicators": self._engine.calculate(cleaned),
        }
