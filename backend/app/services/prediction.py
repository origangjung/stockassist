"""prediction 파일은 애플리케이션 사용 사례 기능을 담당한다."""

from app.adapters.broker import BrokerAdapter
from app.prediction.contracts import PredictionEngine
from app.repositories.contracts import PredictionRepository


class PredictionService:
    """사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다."""

    def __init__(
        self,
        broker: BrokerAdapter,
        engine: PredictionEngine,
        repository: PredictionRepository | None = None,
    ) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._broker = broker
        self._engine = engine
        self._repository = repository

    def predict(self, symbol: str, *, horizon_days: int, limit: int) -> dict:
        """`predict`은(는) 입력 데이터를 기준으로 모델 또는 규칙의 결과 값을 계산해 반환합니다."""

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
