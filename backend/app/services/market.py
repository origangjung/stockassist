"""market 파일은 애플리케이션 사용 사례 기능을 담당한다."""

from app.adapters.broker import BrokerAdapter
from app.pipeline.candles import CandleInterval, CandlePipeline, PipelineResult
from app.providers.contracts import Capability


class MarketDataService:
    """사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다."""

    def __init__(self, broker: BrokerAdapter):
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._broker = broker
        self._pipeline = CandlePipeline()

    def quote(self, symbol: str):
        """`quote`은(는) 이름에 해당하는 시장 또는 기업 데이터를 조회해 공통 형식으로 반환합니다."""

        provider = self._broker.provider_for(Capability.QUOTE)
        return provider.get_quote(symbol), provider.name

    def candles(self, symbol: str, limit: int):
        """`candles`은(는) 이름에 해당하는 시장 또는 기업 데이터를 조회해 공통 형식으로 반환합니다."""

        batch = self._broker.candles(symbol, limit)
        return batch.candles, batch.provider.name

    def orderbook(self, symbol: str):
        """`orderbook`은(는) 이름에 해당하는 시장 또는 기업 데이터를 조회해 공통 형식으로 반환합니다."""

        provider = self._broker.provider_for(Capability.ORDERBOOK)
        asks, bids = provider.get_orderbook(symbol)
        return asks, bids, provider.name

    def trades(self, symbol: str, limit: int):
        """`trades`은(는) 이름에 해당하는 시장 또는 기업 데이터를 조회해 공통 형식으로 반환합니다."""

        provider = self._broker.provider_for(Capability.TRADES)
        return provider.get_trades(symbol, limit), provider.name

    def stock_info(self, symbol: str):
        """`stock_info`은(는) 이름에 해당하는 시장 또는 기업 데이터를 조회해 공통 형식으로 반환합니다."""

        provider = self._broker.provider_for(Capability.QUOTE)
        return provider.get_stock_info(symbol), provider.name

    def warnings(self, symbol: str):
        """`warnings`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        provider = self._broker.provider_for(Capability.WARNINGS)
        return provider.get_warnings(symbol), provider.name

    def processed_candles(
        self, symbol: str, limit: int, interval: CandleInterval
    ) -> tuple[PipelineResult, str]:
        """`processed_candles`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        batch = self._broker.candles(symbol, limit)
        return self._pipeline.process(batch.candles, interval), batch.provider.name
