from app.adapters.broker import BrokerAdapter
from app.indicators import IndicatorEngine
from app.pipeline.candles import CandlePipeline
from app.providers.contracts import Capability


class TechnicalAnalysisService:
    def __init__(self, broker: BrokerAdapter, engine: IndicatorEngine):
        self._broker = broker
        self._engine = engine
        self._pipeline = CandlePipeline()

    def indicators(self, symbol: str, limit: int) -> dict:
        provider = self._broker.provider_for(Capability.CANDLES)
        raw = provider.get_candles(symbol, limit)
        cleaned = self._pipeline.process(raw).cleaned_candles
        return {
            "symbol": symbol,
            "provider": provider.name,
            "engine_version": self._engine.version,
            "validation_status": self._engine.status,
            "indicators": self._engine.calculate(cleaned),
        }
