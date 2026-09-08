"""source 파일은 실시간 시세 연결 기능을 담당한다."""

import asyncio

from app.adapters.broker import BrokerAdapter
from app.providers.contracts import Capability, Quote, StockProvider
from app.realtime.contracts import RealtimeQuoteSource


class PollingQuoteSource(RealtimeQuoteSource):
    """Adapts a synchronous quote provider to the realtime async contract."""

    def __init__(self, broker: BrokerAdapter) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._provider: StockProvider = broker.provider_for(Capability.QUOTE)

    @property
    def name(self) -> str:
        """`name`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        return self._provider.name

    async def validate(self, symbol: str) -> None:
        """`validate`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        await asyncio.to_thread(self._provider.get_stock_info, symbol)

    async def fetch(self, symbol: str) -> Quote:
        """`fetch`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        return await asyncio.to_thread(self._provider.get_quote, symbol)
