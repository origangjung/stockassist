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
    def __init__(
        self,
        broker: BrokerAdapter,
        stocks: StockRepository,
        candles: CandleRepository,
        quality_logs: QualityLogRepository,
        pipeline: CandlePipeline | None = None,
        atomic_repository: CandleIngestionRepository | None = None,
    ):
        self._broker = broker
        self._stocks = stocks
        self._candles = candles
        self._quality_logs = quality_logs
        self._pipeline = pipeline or CandlePipeline()
        self._atomic_repository = atomic_repository

    def ingest_daily(self, symbol: str, limit: int = 120) -> IngestionSummary:
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
