"""ingestion 파일은 애플리케이션 사용 사례 기능을 담당한다."""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from app.adapters.broker import BrokerAdapter
from app.pipeline.candles import CandleInterval, CandlePipeline
from app.repositories.contracts import (
    CandleIngestionRepository,
    CandleIngestionWrite,
    CandleRepository,
    QualityLogRepository,
    StockRepository,
)
from app.config import Settings
from app.providers.errors import ProviderValidationError


@dataclass(frozen=True)
class IngestionSummary:
    """`IngestionSummary` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    symbol: str
    provider: str
    raw_count: int
    cleaned_count: int
    quality_log_count: int
    aggregation_version: str
    price_basis: str
    price_basis_rule_version: str
    price_basis_verification_status: str


class CandleIngestionService:
    """사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다."""

    def __init__(
        self,
        broker: BrokerAdapter,
        stocks: StockRepository,
        candles: CandleRepository,
        quality_logs: QualityLogRepository,
        pipeline: CandlePipeline | None = None,
        atomic_repository: CandleIngestionRepository | None = None,
    ):
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._broker = broker
        self._stocks = stocks
        self._candles = candles
        self._quality_logs = quality_logs
        self._pipeline = pipeline or CandlePipeline()
        self._atomic_repository = atomic_repository

    def ingest_daily(self, symbol: str, limit: int = 120) -> IngestionSummary:
        """`ingest_daily`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        symbol = symbol.strip().upper()
        batch = self._broker.candles(symbol, limit)
        provider = batch.provider
        stock = provider.get_stock_info(symbol)
        if stock.symbol.strip().upper() != symbol:
            raise ProviderValidationError(
                "Provider stock metadata symbol does not match the ingestion request",
                code="stock-symbol-contract-mismatch",
                data={"provider": provider.name, "requested_symbol": symbol},
            )
        raw = batch.candles
        result = self._pipeline.process(raw, CandleInterval.DAY)

        if self._atomic_repository is not None:
            self._atomic_repository.save(
                CandleIngestionWrite(
                    stock=stock,
                    raw_candles=raw,
                    cleaned_candles=result.cleaned_candles,
                    quality_logs=result.quality_logs,
                    interval="1d",
                    cleaned_aggregation_version=result.aggregation_version,
                    source_provider=provider.name,
                    price_basis_rule_version=batch.policy.rule_version,
                )
            )
        else:
            self._stocks.upsert(stock)
            self._candles.save_many(
                symbol,
                raw,
                interval="1d",
                stage="raw",
                aggregation_version="raw",
                source_provider=provider.name,
                price_basis_rule_version=batch.policy.rule_version,
            )
            self._candles.save_many(
                symbol,
                result.cleaned_candles,
                interval="1d",
                stage="cleaned",
                aggregation_version=result.aggregation_version,
                source_provider=provider.name,
                price_basis_rule_version=batch.policy.rule_version,
            )
            self._quality_logs.save_many(symbol, result.quality_logs)
        return IngestionSummary(
            symbol=symbol,
            provider=provider.name,
            raw_count=len(raw),
            cleaned_count=len(result.cleaned_candles),
            quality_log_count=len(result.quality_logs),
            aggregation_version=result.aggregation_version,
            price_basis=batch.policy.expected_basis,
            price_basis_rule_version=batch.policy.rule_version,
            price_basis_verification_status=batch.policy.verification_status,
        )


class IngestionUnavailableError(RuntimeError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    pass


class IngestionOperationsService:
    """사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다."""

    def __init__(
        self,
        settings: Settings,
        ingestion: CandleIngestionService | None,
    ) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._settings = settings
        self._ingestion = ingestion

    def status(self) -> dict[str, object]:
        """`status`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        return {
            "scheduler_enabled": self._settings.scheduler_enabled,
            "persistence_enabled": self._settings.persistence_enabled,
            "manual_ingestion_available": self._ingestion is not None,
            "interval_minutes": self._settings.scheduler_interval_minutes,
            "ingestion_limit": self._settings.scheduler_ingestion_limit,
            "symbols": self._settings.scheduled_symbols,
        }

    def ingest(self, symbol: str, *, limit: int | None = None) -> dict[str, object]:
        """`ingest`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        if self._ingestion is None:
            raise IngestionUnavailableError("Candle persistence is disabled")
        normalized = symbol.strip().upper()
        summary = self._ingestion.ingest_daily(
            normalized,
            limit=limit or self._settings.scheduler_ingestion_limit,
        )
        return {
            "summary": asdict(summary),
            "configured_symbol": normalized in self._settings.scheduled_symbols,
            "triggered_at": datetime.now(UTC),
        }
