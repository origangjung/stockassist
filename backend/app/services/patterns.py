from app.adapters.broker import BrokerAdapter
from app.patterns import PatternEngine
from app.pipeline.candles import CandlePipeline


class PatternAnalysisService:
    def __init__(self, broker: BrokerAdapter, engine: PatternEngine) -> None:
        self._broker = broker
        self._engine = engine
        self._pipeline = CandlePipeline()

    def patterns(self, symbol: str, limit: int) -> dict:
        batch = self._broker.candles(symbol, limit)
        cleaned = self._pipeline.process(batch.candles).cleaned_candles
        return {
            "symbol": symbol,
            "provider": batch.provider.name,
            **self._engine.analyze(cleaned),
        }
