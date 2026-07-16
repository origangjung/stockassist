from fastapi.testclient import TestClient
import pytest

from app.adapters.broker import BrokerAdapter
from app.api.routes import get_ingestion_operations_service
from app.config import Settings, get_settings
from app.main import app
from app.providers.mock import MockProvider
from app.repositories.memory import (
    InMemoryCandleRepository,
    InMemoryQualityLogRepository,
    InMemoryStockRepository,
)
from app.scheduler import build_scheduler
from app.services.ingestion import CandleIngestionService, IngestionOperationsService


def _settings(**overrides: object) -> Settings:
    values = {
        "admin_api_key": "test-admin-secret",
        "persistence_enabled": True,
        "scheduler_enabled": True,
        "scheduler_symbols": "005930, aapl,005930,MSFT",
        "scheduler_ingestion_limit": 75,
        "realtime_enabled": False,
        "stock_provider": "mock",
        "financial_provider": "mock",
        "disclosure_provider": "mock",
        "news_provider": "mock",
        "investor_flow_provider": "mock",
        "ai_report_provider": "mock",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_scheduler_uses_normalized_configured_domestic_and_us_symbols(tmp_path):
    settings = _settings(database_url=f"sqlite:///{tmp_path / 'scheduler.db'}")
    scheduler = build_scheduler(settings, BrokerAdapter([MockProvider()]))

    jobs = {job.id: job for job in scheduler.get_jobs()}
    assert set(jobs) == {
        "daily-candles:005930",
        "daily-candles:AAPL",
        "daily-candles:MSFT",
    }
    assert jobs["daily-candles:AAPL"].kwargs == {"symbol": "AAPL", "limit": 75}


def test_scheduler_configuration_rejects_unsafe_or_unbounded_universes():
    with pytest.raises(ValueError, match="invalid symbol"):
        _settings(scheduler_symbols="005930,../../secret")
    with pytest.raises(ValueError, match="at most 50"):
        _settings(scheduler_symbols=",".join(f"A{index}" for index in range(51)))
    with pytest.raises(ValueError, match="PERSISTENCE_ENABLED"):
        _settings(persistence_enabled=False)


def test_manual_ingestion_persists_supported_us_symbol():
    broker = BrokerAdapter([MockProvider()])
    stocks = InMemoryStockRepository()
    candles = InMemoryCandleRepository()
    quality = InMemoryQualityLogRepository()
    service = IngestionOperationsService(
        _settings(),
        CandleIngestionService(broker, stocks, candles, quality),
    )

    result = service.ingest("aapl", limit=30)

    assert result["summary"]["symbol"] == "AAPL"
    assert result["summary"]["raw_count"] == 30
    assert result["configured_symbol"] is True
    assert "AAPL" in stocks.items


class _StubIngestionOperationsService:
    def status(self) -> dict[str, object]:
        return {
            "scheduler_enabled": False,
            "persistence_enabled": False,
            "manual_ingestion_available": False,
            "interval_minutes": 5,
            "ingestion_limit": 120,
            "symbols": ["005930"],
        }

    def ingest(self, symbol: str, *, limit: int | None = None) -> dict[str, object]:
        return {"summary": {"symbol": symbol, "raw_count": limit or 120}}


def test_ingestion_endpoints_are_admin_only_and_limit_is_bounded():
    app.dependency_overrides[get_settings] = lambda: _settings(scheduler_enabled=False)
    app.dependency_overrides[get_ingestion_operations_service] = (
        _StubIngestionOperationsService
    )
    client = TestClient(app)
    headers = {"X-Admin-Key": "test-admin-secret"}
    try:
        assert client.get("/api/v1/admin/ingestion").status_code == 401
        status = client.get("/api/v1/admin/ingestion", headers=headers)
        triggered = client.post(
            "/api/v1/admin/ingestion/AAPL?limit=30",
            headers=headers,
        )
        invalid = client.post(
            "/api/v1/admin/ingestion/AAPL?limit=1000",
            headers=headers,
        )

        assert status.status_code == 200
        assert triggered.json()["data"]["summary"]["raw_count"] == 30
        assert invalid.status_code == 422
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(get_ingestion_operations_service, None)
