from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.routes import get_provider_audit_history_service
from app.config import Settings, get_settings
from app.database import Base, create_session_factory
from app.main import app
from app.providers.audit import ProviderAuditEvent
from app.repositories.provider_audit import SqlAlchemyProviderAuditRepository
from app.services.provider_audit import ProviderAuditHistoryService


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


def _event(*, outcome: str, request_id: str) -> ProviderAuditEvent:
    return ProviderAuditEvent(
        provider="toss",
        method="GET",
        endpoint="/api/v1/prices",
        api_group="MARKET_DATA",
        outcome=outcome,
        status_code=200 if outcome == "success" else 404,
        error_code=None if outcome == "success" else "stock-not-found",
        provider_request_id=request_id,
        internal_request_id="internal-request",
        attempt_count=1,
        duration_ms=12.5,
        occurred_at=datetime(2026, 7, 16, tzinfo=UTC),
    )


def test_provider_audit_repository_persists_and_filters(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'provider-audit.db'}")
    Base.metadata.create_all(sessions.kw["bind"])
    repository = SqlAlchemyProviderAuditRepository(sessions)
    repository.save(_event(outcome="success", request_id="req-success"))
    repository.save(_event(outcome="error", request_id="req-error"))

    items, total = repository.list_recent(
        limit=10,
        offset=0,
        provider="toss",
        outcome="error",
    )

    assert total == 1
    assert len(items) == 1
    assert items[0].provider_request_id == "req-error"
    assert items[0].internal_request_id == "internal-request"


def test_provider_audit_service_reports_disabled_persistence():
    result = ProviderAuditHistoryService(None).recent(limit=25, offset=0)

    assert result == {
        "persistence_status": "disabled",
        "items": [],
        "total": 0,
        "limit": 25,
        "offset": 0,
    }


class _StubProviderAuditService:
    def recent(self, **_: object) -> dict[str, object]:
        return {
            "persistence_status": "enabled",
            "items": [],
            "total": 0,
            "limit": 50,
            "offset": 0,
        }


def test_provider_audit_endpoint_is_admin_only_and_validates_filters():
    app.dependency_overrides[get_settings] = _settings
    app.dependency_overrides[get_provider_audit_history_service] = _StubProviderAuditService
    client = TestClient(app)
    headers = {"X-Admin-Key": "test-admin-secret"}
    try:
        assert client.get("/api/v1/admin/provider-audits").status_code == 401
        accepted = client.get(
            "/api/v1/admin/provider-audits?provider=toss&outcome=error",
            headers=headers,
        )
        invalid = client.get(
            "/api/v1/admin/provider-audits?outcome=retrying",
            headers=headers,
        )

        assert accepted.status_code == 200
        assert accepted.json()["data"]["persistence_status"] == "enabled"
        assert invalid.status_code == 422
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(get_provider_audit_history_service, None)
