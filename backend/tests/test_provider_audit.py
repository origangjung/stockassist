from datetime import UTC, datetime

from fastapi.testclient import TestClient

import pytest

from app.adapters.broker import BrokerAdapter
from app.api.routes import (
    get_provider_audit_history_service,
    get_provider_audit_maintenance_service,
)
from app.config import Settings, get_settings
from app.database import Base, create_session_factory
from app.main import app
from app.providers.audit import ProviderAuditEvent
from app.providers.mock import MockProvider
from app.repositories.provider_audit import SqlAlchemyProviderAuditRepository
from app.scheduler import build_scheduler
from app.services.provider_audit import (
    ProviderAuditHistoryService,
    ProviderAuditMaintenanceService,
)


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


def _event(
    *,
    outcome: str,
    request_id: str,
    occurred_at: datetime | None = None,
) -> ProviderAuditEvent:
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
        occurred_at=occurred_at or datetime(2026, 7, 16, tzinfo=UTC),
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


def test_provider_audit_repository_deletes_only_records_before_cutoff(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'provider-retention.db'}")
    Base.metadata.create_all(sessions.kw["bind"])
    repository = SqlAlchemyProviderAuditRepository(sessions)
    repository.save(
        _event(
            outcome="success",
            request_id="req-expired",
            occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    repository.save(
        _event(
            outcome="success",
            request_id="req-retained",
            occurred_at=datetime(2026, 7, 1, tzinfo=UTC),
        )
    )

    deleted = repository.delete_before(datetime(2026, 6, 1, tzinfo=UTC))
    items, total = repository.list_recent(limit=10, offset=0)

    assert deleted == 1
    assert total == 1
    assert items[0].provider_request_id == "req-retained"


def test_provider_audit_service_reports_disabled_persistence():
    result = ProviderAuditHistoryService(None).recent(limit=25, offset=0)

    assert result == {
        "persistence_status": "disabled",
        "items": [],
        "total": 0,
        "limit": 25,
        "offset": 0,
    }


def test_provider_audit_maintenance_deletes_expired_records_and_reports_status(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'provider-cleanup.db'}")
    Base.metadata.create_all(sessions.kw["bind"])
    repository = SqlAlchemyProviderAuditRepository(sessions)
    repository.save(
        _event(
            outcome="success",
            request_id="req-expired",
            occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    service = ProviderAuditMaintenanceService(
        repository,
        enabled=True,
        retention_days=90,
        cleanup_hour_kst=4,
    )

    result = service.cleanup(datetime(2026, 7, 19, tzinfo=UTC))

    assert result["status"] == "healthy"
    assert result["last_deleted_count"] == 1
    assert result["last_cutoff"] == datetime(2026, 4, 20, tzinfo=UTC)
    assert repository.list_recent(limit=10, offset=0)[1] == 0


class _FailingMaintenanceRepository:
    def delete_before(self, _: datetime) -> int:
        raise RuntimeError("database unavailable")


def test_provider_audit_maintenance_contains_repository_failure():
    service = ProviderAuditMaintenanceService(
        _FailingMaintenanceRepository(),
        enabled=True,
        retention_days=90,
        cleanup_hour_kst=4,
    )

    result = service.cleanup(datetime(2026, 7, 19, tzinfo=UTC))

    assert result["status"] == "failed"
    assert result["last_error_type"] == "RuntimeError"
    assert "database unavailable" not in str(result)


def test_provider_audit_cleanup_requires_persistence():
    with pytest.raises(ValueError, match="PROVIDER_AUDIT_CLEANUP_ENABLED"):
        Settings(
            _env_file=None,
            persistence_enabled=False,
            provider_audit_cleanup_enabled=True,
        )


def test_provider_audit_cleanup_scheduler_runs_daily(tmp_path):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'audit-scheduler.db'}",
        persistence_enabled=True,
        provider_audit_cleanup_enabled=True,
        provider_audit_retention_days=120,
        provider_audit_cleanup_hour_kst=5,
    )
    service = ProviderAuditMaintenanceService(
        None,
        enabled=False,
        retention_days=120,
        cleanup_hour_kst=5,
    )

    scheduler = build_scheduler(
        settings,
        BrokerAdapter([MockProvider()]),
        provider_audit_service=service,
    )

    job = scheduler.get_job("provider-audit-cleanup")
    assert job is not None
    assert str(job.trigger) == "cron[hour='5', minute='15']"
    assert job.next_run_time is not None


class _StubProviderAuditService:
    def recent(self, **_: object) -> dict[str, object]:
        return {
            "persistence_status": "enabled",
            "items": [],
            "total": 0,
            "limit": 50,
            "offset": 0,
        }


class _StubProviderAuditMaintenanceService:
    def cleanup(self) -> dict[str, object]:
        return {
            "status": "healthy",
            "enabled": True,
            "retention_days": 90,
            "last_deleted_count": 3,
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


def test_provider_audit_cleanup_endpoint_is_admin_only():
    app.dependency_overrides[get_settings] = _settings
    app.dependency_overrides[get_provider_audit_maintenance_service] = (
        _StubProviderAuditMaintenanceService
    )
    client = TestClient(app)
    headers = {"X-Admin-Key": "test-admin-secret"}
    try:
        unauthorized = client.post("/api/v1/admin/provider-audits/cleanup")
        accepted = client.post(
            "/api/v1/admin/provider-audits/cleanup",
            headers=headers,
        )

        assert unauthorized.status_code == 401
        assert accepted.status_code == 200
        assert accepted.json()["data"]["last_deleted_count"] == 3
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(get_provider_audit_maintenance_service, None)
