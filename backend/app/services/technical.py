"""technical 파일은 애플리케이션 사용 사례 기능을 담당한다."""

from app.adapters.broker import BrokerAdapter
from app.indicators import IndicatorEngine
from app.pipeline.candles import CandlePipeline


class TechnicalAnalysisService:
    """사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다."""

    def __init__(self, broker: BrokerAdapter, engine: IndicatorEngine):
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._broker = broker
        self._engine = engine
        self._pipeline = CandlePipeline()

    def indicators(self, symbol: str, limit: int) -> dict:
        """`indicators`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        batch = self._broker.candles(symbol, limit)
        cleaned = self._pipeline.process(batch.candles).cleaned_candles
        return {
            "symbol": symbol,
            "provider": batch.provider.name,
            "engine_version": self._engine.version,
            "validation_status": self._engine.status,
            "indicators": self._engine.calculate(cleaned),
        }
