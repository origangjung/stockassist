import asyncio

from app.adapters.broker import BrokerAdapter
from app.providers.contracts import Capability, Quote, StockProvider
from app.realtime.contracts import RealtimeQuoteSource


class PollingQuoteSource(RealtimeQuoteSource):
    """Adapts a synchronous quote provider to the realtime async contract."""

    def __init__(self, broker: BrokerAdapter) -> None:
        self._provider: StockProvider = broker.provider_for(Capability.QUOTE)

    @property
    def name(self) -> str:
        return self._provider.name

    async def validate(self, symbol: str) -> None:
        await asyncio.to_thread(self._provider.get_stock_info, symbol)

    async def fetch(self, symbol: str) -> Quote:
        return await asyncio.to_thread(self._provider.get_quote, symbol)
