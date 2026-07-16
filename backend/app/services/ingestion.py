from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from app.adapters.broker import BrokerAdapter
from app.pipeline.candles import CandleInterval, CandlePipeline
from app.providers.contracts import Capability
from app.repositories.contracts import CandleRepository, QualityLogRepository, StockRepository
from app.config import Settings


@dataclass(frozen=True)
class IngestionSummary:
    symbol: str
    provider: str
    raw_count: int
    cleaned_count: int
    quality_log_count: int
    aggregation_version: str


class CandleIngestionService:
    def __init__(
        self,
        broker: BrokerAdapter,
        stocks: StockRepository,
        candles: CandleRepository,
        quality_logs: QualityLogRepository,
        pipeline: CandlePipeline | None = None,
    ):
        self._broker = broker
        self._stocks = stocks
        self._candles = candles
        self._quality_logs = quality_logs
        self._pipeline = pipeline or CandlePipeline()

    def ingest_daily(self, symbol: str, limit: int = 120) -> IngestionSummary:
        provider = self._broker.provider_for(Capability.CANDLES)
        stock = provider.get_stock_info(symbol)
        raw = provider.get_candles(symbol, limit)
        result = self._pipeline.process(raw, CandleInterval.DAY)

        self._stocks.upsert(stock)
        self._candles.save_many(symbol, raw, interval="1d", stage="raw", aggregation_version="raw")
        self._candles.save_many(
            symbol,
            result.cleaned_candles,
            interval="1d",
            stage="cleaned",
            aggregation_version=result.aggregation_version,
        )
        self._quality_logs.save_many(symbol, result.quality_logs)
        return IngestionSummary(
            symbol=symbol,
            provider=provider.name,
            raw_count=len(raw),
            cleaned_count=len(result.cleaned_candles),
            quality_log_count=len(result.quality_logs),
            aggregation_version=result.aggregation_version,
        )


class IngestionUnavailableError(RuntimeError):
    pass


class IngestionOperationsService:
    def __init__(
        self,
        settings: Settings,
        ingestion: CandleIngestionService | None,
    ) -> None:
        self._settings = settings
        self._ingestion = ingestion

    def status(self) -> dict[str, object]:
        return {
            "scheduler_enabled": self._settings.scheduler_enabled,
            "persistence_enabled": self._settings.persistence_enabled,
            "manual_ingestion_available": self._ingestion is not None,
            "interval_minutes": self._settings.scheduler_interval_minutes,
            "ingestion_limit": self._settings.scheduler_ingestion_limit,
            "symbols": self._settings.scheduled_symbols,
        }

    def ingest(self, symbol: str, *, limit: int | None = None) -> dict[str, object]:
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
