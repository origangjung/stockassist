import asyncio

from fastapi.testclient import TestClient

from app.api.routes import get_operations_status_service
from app.config import Settings, get_settings
from app.main import app
from app.observability.health import DependencySpec, HealthService
from app.services.operations import OperationsStatusService


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        admin_api_key="test-admin-secret",
        toss_client_secret="never-expose-toss-secret",
        openai_api_key="never-expose-openai-secret",
        sentry_dsn="https://private@sentry.example.test/1",
        persistence_enabled=True,
        realtime_enabled=False,
        scheduler_enabled=True,
        stock_provider="mock",
        financial_provider="mock",
        disclosure_provider="mock",
        news_provider="mock",
        investor_flow_provider="mock",
        ai_report_provider="mock",
        prediction_engine="lightweight",
    )


def test_operations_status_reports_safe_runtime_configuration_without_secrets():
    health = HealthService(
        [
            DependencySpec("database", False, None),
            DependencySpec("redis", False, None),
        ]
    )
    result = asyncio.run(OperationsStatusService(_settings(), health).status())

    assert result["status"] == "operational"
    assert result["ready"] is True
    assert result["providers"]["market"] == "mock"
    assert result["providers"]["prediction"] == "lightweight"
    assert result["features"]["scheduler"] is True
    assert result["features"]["sentry"] is True
    assert result["features"]["distributed_rate_limit"] is False
    assert result["features"]["provider_audit_cleanup"] is False
    assert result["provider_audit"]["status"] == "disabled"
    assert result["features"]["data_lifecycle_cleanup"] is False
    assert result["data_lifecycle"]["status"] == "disabled"
    serialized = str(result)
    assert "never-expose-toss-secret" not in serialized
    assert "never-expose-openai-secret" not in serialized
    assert "private@sentry" not in serialized


class _StubOperationsStatusService:
    async def status(self) -> dict[str, object]:
        return {
            "status": "operational",
            "ready": True,
            "service": "stockpilot-api",
            "release": "test@1",
            "environment": "test",
            "checked_at": "2026-07-16T00:00:00Z",
            "readiness": {"status": "ready", "checks": {}},
            "providers": {},
            "features": {},
            "realtime": {},
        }


def test_operations_status_endpoint_requires_admin_access():
    settings = _settings()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_operations_status_service] = _StubOperationsStatusService
    client = TestClient(app)
    try:
        unauthorized = client.get("/api/v1/admin/operations/status")
        accepted = client.get(
            "/api/v1/admin/operations/status",
            headers={"X-Admin-Key": "test-admin-secret"},
        )

        assert unauthorized.status_code == 401
        assert accepted.status_code == 200
        assert accepted.json()["data"]["ready"] is True
        assert accepted.headers["Cache-Control"] == "no-store, private"
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(get_operations_status_service, None)
