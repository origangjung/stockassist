from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.routes import get_data_quality_history_service
from app.config import Settings, get_settings
from app.database import Base, create_session_factory
from app.main import app
from app.pipeline.candles import DataQualityLog, QualitySeverity
from app.repositories.sqlalchemy import SqlAlchemyQualityLogRepository
from app.services.data_quality import DataQualityHistoryService


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        admin_api_key="test-admin-secret",
        persistence_enabled=False,
        realtime_enabled=False,
        stock_provider="mock",
        financial_provider="mock",
        disclosure_provider="mock",
        news_provider="mock",
        investor_flow_provider="mock",
        ai_report_provider="mock",
    )


def test_quality_log_repository_filters_and_counts_recent_records(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'quality.db'}")
    Base.metadata.create_all(sessions.kw["bind"])
    repository = SqlAlchemyQualityLogRepository(sessions)
    observed = datetime(2026, 7, 16, tzinfo=UTC)
    repository.save_many(
        "005930",
        [
            DataQualityLog("invalid_ohlc", QualitySeverity.ERROR, "invalid", observed),
            DataQualityLog("missing_candle", QualitySeverity.WARNING, "missing", observed),
        ],
    )
    repository.save_many(
        "AAPL",
        [DataQualityLog("duplicate_timestamp", QualitySeverity.ERROR, "duplicate", observed)],
    )

    items, total, counts = repository.list_recent(
        limit=10,
        offset=0,
        symbol="005930",
    )
    errors, error_total, error_counts = repository.list_recent(
        limit=10,
        offset=0,
        severity="error",
    )

    assert total == 2
    assert {item.rule for item in items} == {"invalid_ohlc", "missing_candle"}
    assert counts == {"error": 1, "warning": 1}
    assert error_total == 2
    assert all(item.severity == QualitySeverity.ERROR for item in errors)
    assert error_counts == {"error": 2}


def test_quality_history_service_reports_disabled_persistence():
    result = DataQualityHistoryService(None).recent(limit=25, offset=0)

    assert result == {
        "persistence_status": "disabled",
        "items": [],
        "total": 0,
        "severity_counts": {"error": 0, "warning": 0},
        "limit": 25,
        "offset": 0,
    }


class _StubDataQualityService:
    def recent(self, **_: object) -> dict[str, object]:
        return {
            "persistence_status": "enabled",
            "items": [],
            "total": 0,
            "severity_counts": {"error": 0, "warning": 0},
            "limit": 50,
            "offset": 0,
        }


def test_data_quality_endpoint_is_admin_only_and_validates_filters():
    app.dependency_overrides[get_settings] = _settings
    app.dependency_overrides[get_data_quality_history_service] = _StubDataQualityService
    client = TestClient(app)
    headers = {"X-Admin-Key": "test-admin-secret"}
    try:
        assert client.get("/api/v1/admin/data-quality").status_code == 401
        accepted = client.get(
            "/api/v1/admin/data-quality?symbol=005930&severity=error",
            headers=headers,
        )
        invalid = client.get(
            "/api/v1/admin/data-quality?severity=critical",
            headers=headers,
        )

        assert accepted.status_code == 200
        assert accepted.json()["data"]["persistence_status"] == "enabled"
        assert invalid.status_code == 422
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(get_data_quality_history_service, None)
