from app.adapters.broker import BrokerAdapter
from app.patterns import PatternEngine
from app.pipeline.candles import CandlePipeline
from app.providers.contracts import Capability


class PatternAnalysisService:
    def __init__(self, broker: BrokerAdapter, engine: PatternEngine) -> None:
        self._broker = broker
        self._engine = engine
        self._pipeline = CandlePipeline()

    def patterns(self, symbol: str, limit: int) -> dict:
        provider = self._broker.provider_for(Capability.CANDLES)
        raw = provider.get_candles(symbol, limit)
        cleaned = self._pipeline.process(raw).cleaned_candles
        return {
            "symbol": symbol,
            "provider": provider.name,
            **self._engine.analyze(cleaned),
        }
