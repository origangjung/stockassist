from dataclasses import replace

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.broker import BrokerAdapter
from app.database import Base, create_session_factory
from app.models.market import DataQualityLogModel, StockCandleModel, StockModel
from app.providers.mock import MockProvider
from app.providers.errors import ProviderValidationError
from app.repositories.memory import (
    InMemoryCandleRepository,
    InMemoryQualityLogRepository,
    InMemoryStockRepository,
)
from app.services.ingestion import CandleIngestionService
from app.repositories.sqlalchemy import SqlAlchemyCandleIngestionRepository


class _MismatchedStockProvider(MockProvider):
    def get_stock_info(self, symbol: str):
        return replace(super().get_stock_info(symbol), symbol="AAPL")


def test_ingestion_persists_raw_and_cleaned_stages_idempotently():
    stocks = InMemoryStockRepository()
    candles = InMemoryCandleRepository()
    quality = InMemoryQualityLogRepository()
    service = CandleIngestionService(BrokerAdapter([MockProvider()]), stocks, candles, quality)

    first = service.ingest_daily("005930", limit=30)
    second = service.ingest_daily("005930", limit=30)

    assert first.raw_count == first.cleaned_count == 30
    assert first.price_basis == "unadjusted"
    assert first.price_basis_rule_version == "mock-candles-v1"
    assert first.price_basis_verification_status == "synthetic"
    assert second.raw_count == 30
    assert len(candles.find("005930", interval="1d", stage="raw", limit=100)) == 30
    assert len(candles.find("005930", interval="1d", stage="cleaned", limit=100)) == 30
    assert "005930" in stocks.items
    assert set(candles.sources[("005930", "1d", "raw", "raw")].values()) == {"mock"}
    assert set(
        candles.sources[("005930", "1d", "cleaned", first.aggregation_version)].values()
    ) == {"mock"}
    assert set(candles.price_basis_rules[("005930", "1d", "raw", "raw")].values()) == {
        "mock-candles-v1"
    }


def test_ingestion_rejects_mismatched_stock_metadata_before_persistence():
    stocks = InMemoryStockRepository()
    candles = InMemoryCandleRepository()
    quality = InMemoryQualityLogRepository()
    service = CandleIngestionService(
        BrokerAdapter([_MismatchedStockProvider()]), stocks, candles, quality
    )

    with pytest.raises(ProviderValidationError, match="does not match"):
        service.ingest_daily("005930", limit=30)

    assert stocks.items == {}
    assert candles.items == {}
    assert quality.items == []


class _FailingAtomicIngestionRepository(SqlAlchemyCandleIngestionRepository):
    @staticmethod
    def _save_quality_logs(
        session: Session,
        symbol: str,
        logs: list,
    ) -> None:
        del session, symbol, logs
        raise RuntimeError("simulated quality-log write failure")


def test_sql_ingestion_rolls_back_stock_and_candles_when_final_write_fails(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'atomic-ingestion.db'}")
    Base.metadata.create_all(sessions.kw["bind"])
    stocks = InMemoryStockRepository()
    candles = InMemoryCandleRepository()
    quality = InMemoryQualityLogRepository()
    service = CandleIngestionService(
        BrokerAdapter([MockProvider()]),
        stocks,
        candles,
        quality,
        atomic_repository=_FailingAtomicIngestionRepository(sessions),
    )

    with pytest.raises(RuntimeError, match="simulated quality-log write failure"):
        service.ingest_daily("005930", limit=30)

    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(StockModel)) == 0
        assert session.scalar(select(func.count()).select_from(StockCandleModel)) == 0
        assert session.scalar(select(func.count()).select_from(DataQualityLogModel)) == 0
