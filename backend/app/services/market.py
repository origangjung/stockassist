from app.adapters.broker import BrokerAdapter
from app.pipeline.candles import CandleInterval, CandlePipeline, PipelineResult
from app.providers.contracts import Capability


class MarketDataService:
    def __init__(self, broker: BrokerAdapter):
        self._broker = broker
        self._pipeline = CandlePipeline()

    def quote(self, symbol: str):
        provider = self._broker.provider_for(Capability.QUOTE)
        return provider.get_quote(symbol), provider.name

    def candles(self, symbol: str, limit: int):
        batch = self._broker.candles(symbol, limit)
        return batch.candles, batch.provider.name

    def orderbook(self, symbol: str):
        provider = self._broker.provider_for(Capability.ORDERBOOK)
        asks, bids = provider.get_orderbook(symbol)
        return asks, bids, provider.name

    def trades(self, symbol: str, limit: int):
        provider = self._broker.provider_for(Capability.TRADES)
        return provider.get_trades(symbol, limit), provider.name

    def stock_info(self, symbol: str):
        provider = self._broker.provider_for(Capability.QUOTE)
        return provider.get_stock_info(symbol), provider.name

    def warnings(self, symbol: str):
        provider = self._broker.provider_for(Capability.WARNINGS)
        return provider.get_warnings(symbol), provider.name

    def processed_candles(
        self, symbol: str, limit: int, interval: CandleInterval
    ) -> tuple[PipelineResult, str]:
        batch = self._broker.candles(symbol, limit)
        return self._pipeline.process(batch.candles, interval), batch.provider.name
