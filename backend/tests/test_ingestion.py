from app.adapters.broker import BrokerAdapter
from app.providers.mock import MockProvider
from app.repositories.memory import (
    InMemoryCandleRepository,
    InMemoryQualityLogRepository,
    InMemoryStockRepository,
)
from app.services.ingestion import CandleIngestionService


def test_ingestion_persists_raw_and_cleaned_stages_idempotently():
    stocks = InMemoryStockRepository()
    candles = InMemoryCandleRepository()
    quality = InMemoryQualityLogRepository()
    service = CandleIngestionService(BrokerAdapter([MockProvider()]), stocks, candles, quality)

    first = service.ingest_daily("005930", limit=30)
    second = service.ingest_daily("005930", limit=30)

    assert first.raw_count == first.cleaned_count == 30
    assert second.raw_count == 30
    assert len(candles.find("005930", interval="1d", stage="raw", limit=100)) == 30
    assert len(candles.find("005930", interval="1d", stage="cleaned", limit=100)) == 30
    assert "005930" in stocks.items
