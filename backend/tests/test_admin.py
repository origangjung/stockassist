from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from redis.exceptions import RedisError

import pytest

from app.config import Settings, get_settings
from app.main import app
from app.adapters.broker import BrokerAdapter
from app.alerts import InMemoryAlertRepository
from app.api.routes import get_model_registry_service, get_reference_alert_service
from app.providers.mock import MockProvider
from app.services.alerts import ReferenceAlertService
from app.services.model_registry import ModelRegistryService
from app.api.admin import require_admin_access, reset_admin_rate_limiter


def _settings(admin_api_key: str | None) -> Settings:
    return Settings(
        _env_file=None,
        admin_api_key=admin_api_key,
        persistence_enabled=False,
        stock_provider="mock",
        financial_provider="mock",
        disclosure_provider="mock",
        news_provider="mock",
        investor_flow_provider="mock",
        ai_report_provider="mock",
        realtime_enabled=False,
    )


def test_admin_api_is_closed_when_key_is_not_configured():
    app.dependency_overrides[get_settings] = lambda: _settings(None)
    try:
        response = TestClient(app).get("/api/v1/admin/backtests")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "HTTP_503"
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_admin_api_rejects_invalid_key_and_accepts_valid_key():
    app.dependency_overrides[get_settings] = lambda: _settings("test-admin-secret")
    client = TestClient(app)
    try:
        unauthorized = client.get(
            "/api/v1/admin/backtests",
            headers={"X-Admin-Key": "wrong"},
        )
        accepted = client.get(
            "/api/v1/admin/backtests",
            headers={"X-Admin-Key": "test-admin-secret"},
        )
        assert unauthorized.status_code == 401
        assert accepted.status_code == 200
        assert accepted.json()["data"] == {
            "persistence_status": "disabled",
            "items": [],
            "total": 0,
            "limit": 25,
            "offset": 0,
        }
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_admin_watchlist_and_alert_endpoints_are_protected_and_report_disabled_storage():
    app.dependency_overrides[get_settings] = lambda: _settings("test-admin-secret")
    app.dependency_overrides[get_reference_alert_service] = lambda: ReferenceAlertService(
        BrokerAdapter([MockProvider()]),
        None,
    )
    client = TestClient(app)
    headers = {"X-Admin-Key": "test-admin-secret"}
    try:
        assert client.get("/api/v1/admin/watchlist").status_code == 401
        watchlist = client.get("/api/v1/admin/watchlist", headers=headers)
        alerts = client.get("/api/v1/admin/alerts", headers=headers)
        create = client.post(
            "/api/v1/admin/alerts",
            headers=headers,
            json={"symbol": "005930", "condition": "above", "target_price": 80000},
        )
        assert watchlist.status_code == 200
        assert watchlist.json()["data"] == {
            "persistence_status": "disabled",
            "items": [],
        }
        assert alerts.status_code == 200
        assert create.status_code == 503
        assert create.json()["error"]["code"] == "HTTP_503"
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(get_reference_alert_service, None)


def test_admin_reference_alert_round_trip_never_executes_an_order():
    app.dependency_overrides[get_settings] = lambda: _settings("test-admin-secret")
    service = ReferenceAlertService(
        BrokerAdapter([MockProvider()]),
        InMemoryAlertRepository(),
    )
    app.dependency_overrides[get_reference_alert_service] = lambda: service
    client = TestClient(app)
    headers = {"X-Admin-Key": "test-admin-secret"}
    try:
        added = client.post(
            "/api/v1/admin/watchlist",
            headers=headers,
            json={"symbol": "AAPL"},
        )
        created = client.post(
            "/api/v1/admin/alerts",
            headers=headers,
            json={"symbol": "AAPL", "condition": "above", "target_price": 200},
        )
        evaluated = client.post("/api/v1/admin/alerts/evaluate", headers=headers)

        assert added.status_code == 200
        assert added.json()["data"]["item"]["currency"] == "USD"
        assert created.status_code == 200
        assert created.json()["data"]["execution_enabled"] is False
        assert evaluated.status_code == 200
        assert len(evaluated.json()["data"]["triggered"]) == 1
        assert evaluated.json()["data"]["execution_enabled"] is False
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(get_reference_alert_service, None)


def test_admin_authentication_rate_limits_repeated_failures():
    settings = _settings("test-admin-secret")
    settings.admin_max_failed_attempts = 3
    settings.admin_lockout_seconds = 60
    app.dependency_overrides[get_settings] = lambda: settings
    client = TestClient(app)
    try:
        statuses = [
            client.get(
                "/api/v1/admin/backtests",
                headers={"X-Admin-Key": "wrong"},
            ).status_code
            for _ in range(3)
        ]
        blocked_valid = client.get(
            "/api/v1/admin/backtests",
            headers={"X-Admin-Key": "test-admin-secret"},
        )
        assert statuses == [401, 401, 429]
        assert blocked_valid.status_code == 429
        assert blocked_valid.headers["Retry-After"] == "60"

        reset_admin_rate_limiter()
        accepted = client.get(
            "/api/v1/admin/backtests",
            headers={"X-Admin-Key": "test-admin-secret"},
        )
        assert accepted.status_code == 200
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_admin_lockout_uses_distinct_trusted_proxy_client_ips():
    settings = _settings("test-admin-secret")
    settings.admin_max_failed_attempts = 3
    settings.trust_proxy_headers = True
    test_app = FastAPI()
    test_app.dependency_overrides[get_settings] = lambda: settings

    @test_app.get("/admin", dependencies=[Depends(require_admin_access)])
    def protected():
        return {"ok": True}

    client = TestClient(test_app)
    primary_headers = {"X-Admin-Key": "wrong", "X-Real-IP": "203.0.113.10"}
    secondary_headers = {"X-Admin-Key": "wrong", "X-Real-IP": "203.0.113.11"}

    primary_statuses = [client.get("/admin", headers=primary_headers).status_code for _ in range(3)]
    secondary = client.get("/admin", headers=secondary_headers)
    secondary_valid = client.get(
        "/admin",
        headers={"X-Admin-Key": "test-admin-secret", "X-Real-IP": "203.0.113.11"},
    )
    primary_valid = client.get(
        "/admin",
        headers={"X-Admin-Key": "test-admin-secret", "X-Real-IP": "203.0.113.10"},
    )

    assert primary_statuses == [401, 401, 429]
    assert secondary.status_code == 401
    assert secondary_valid.status_code == 200
    assert primary_valid.status_code == 429


def test_admin_lockout_ignores_forwarded_ip_when_proxy_headers_are_not_trusted():
    settings = _settings("test-admin-secret")
    settings.admin_max_failed_attempts = 3
    settings.trust_proxy_headers = False
    test_app = FastAPI()
    test_app.dependency_overrides[get_settings] = lambda: settings

    @test_app.get("/admin", dependencies=[Depends(require_admin_access)])
    def protected():
        return {"ok": True}

    client = TestClient(test_app)
    attempts = [
        client.get(
            "/admin",
            headers={"X-Admin-Key": "wrong", "X-Real-IP": f"203.0.113.{index}"},
        ).status_code
        for index in range(10, 13)
    ]
    spoofed_valid = client.get(
        "/admin",
        headers={"X-Admin-Key": "test-admin-secret", "X-Real-IP": "198.51.100.99"},
    )

    assert attempts == [401, 401, 429]
    assert spoofed_valid.status_code == 429


def test_admin_lockout_rejects_invalid_or_oversized_trusted_proxy_ips():
    settings = _settings("test-admin-secret")
    settings.admin_max_failed_attempts = 3
    settings.trust_proxy_headers = True
    test_app = FastAPI()
    test_app.dependency_overrides[get_settings] = lambda: settings

    @test_app.get("/admin", dependencies=[Depends(require_admin_access)])
    def protected():
        return {"ok": True}

    client = TestClient(test_app)
    invalid_headers = (
        "203.0.113.10, 203.0.113.11",
        "not-an-ip",
        "a" * 65,
    )
    statuses = [
        client.get(
            "/admin",
            headers={"X-Admin-Key": "wrong", "X-Real-IP": real_ip},
        ).status_code
        for real_ip in invalid_headers
    ]

    assert statuses == [401, 401, 429]


def test_distributed_admin_authentication_lockout_and_successful_reset():
    class DistributedLimiter:
        def __init__(self):
            self.attempts = 0

        async def is_limited(self, key: str, *, limit: int, window: int):
            return self.attempts >= limit

        async def consume(self, key: str, *, limit: int, window: int):
            if self.attempts >= limit:
                return False, 0, window
            self.attempts += 1
            return True, max(0, limit - self.attempts), 0

        async def clear(self, key: str):
            self.attempts = 0

    settings = _settings("test-admin-secret")
    settings.rate_limit_backend = "redis"
    settings.admin_max_failed_attempts = 3
    test_app = FastAPI()
    limiter = DistributedLimiter()
    test_app.state.distributed_rate_limiter = limiter
    test_app.dependency_overrides[get_settings] = lambda: settings

    @test_app.get("/admin", dependencies=[Depends(require_admin_access)])
    def protected():
        return {"ok": True}

    client = TestClient(test_app)
    assert client.get("/admin", headers={"X-Admin-Key": "wrong"}).status_code == 401
    assert client.get("/admin", headers={"X-Admin-Key": "test-admin-secret"}).status_code == 200
    assert limiter.attempts == 0
    statuses = [
        client.get("/admin", headers={"X-Admin-Key": "wrong"}).status_code
        for _ in range(3)
    ]
    blocked_valid = client.get("/admin", headers={"X-Admin-Key": "test-admin-secret"})

    assert statuses == [401, 401, 429]
    assert blocked_valid.status_code == 429


def test_distributed_admin_authentication_fails_closed_on_redis_error():
    class UnavailableLimiter:
        async def is_limited(self, key: str, *, limit: int, window: int):
            raise RedisError("secret redis address")

    settings = _settings("test-admin-secret")
    settings.rate_limit_backend = "redis"
    test_app = FastAPI()
    test_app.state.distributed_rate_limiter = UnavailableLimiter()
    test_app.dependency_overrides[get_settings] = lambda: settings

    @test_app.get("/admin", dependencies=[Depends(require_admin_access)])
    def protected():
        return {"ok": True}

    response = TestClient(test_app).get(
        "/admin",
        headers={"X-Admin-Key": "test-admin-secret"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Admin authentication limiter is unavailable"
    assert "secret redis address" not in response.text


def test_admin_model_registry_is_protected_and_fails_closed_without_persistence():
    app.dependency_overrides[get_settings] = lambda: _settings("test-admin-secret")
    app.dependency_overrides[get_model_registry_service] = lambda: ModelRegistryService(None)
    client = TestClient(app)
    headers = {"X-Admin-Key": "test-admin-secret"}
    try:
        assert client.get("/api/v1/admin/models").status_code == 401
        listed = client.get("/api/v1/admin/models", headers=headers)
        promoted = client.post(
            "/api/v1/admin/models/missing/promote",
            headers=headers,
        )
        assert listed.status_code == 200
        assert listed.json()["data"]["persistence_status"] == "disabled"
        assert promoted.status_code == 503
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(get_model_registry_service, None)


def test_production_sensitive_features_require_a_strong_admin_key():
    with pytest.raises(ValueError, match=r"32\+ character"):
        Settings(
            _env_file=None,
            app_environment="production",
            account_sync_enabled=True,
            admin_api_key="short",
        )


def test_production_rejects_weak_admin_key_even_when_sensitive_features_are_disabled():
    with pytest.raises(ValueError, match=r"32\+ characters"):
        Settings(
            _env_file=None,
            app_environment="production",
            admin_api_key="short",
        )


def test_production_rejects_sqlite_persistence_and_insecure_active_provider_url():
    with pytest.raises(ValueError, match="requires PostgreSQL"):
        Settings(
            _env_file=None,
            app_environment="production",
            admin_api_key="a" * 32,
            persistence_enabled=True,
            database_url="sqlite:///./production.db",
        )


def test_allowed_hosts_are_normalized_and_production_rejects_global_wildcard():
    settings = Settings(_env_file=None, allowed_hosts="LOCALHOST, api.example.test,localhost")
    assert settings.trusted_hosts == ["localhost", "api.example.test"]

    with pytest.raises(ValueError, match="must not contain a wildcard"):
        Settings(
            _env_file=None,
            app_environment="production",
            admin_api_key="a" * 32,
            allowed_hosts="*",
        )


def test_production_requires_a_strong_analysis_api_key():
    with pytest.raises(ValueError, match=r"ANALYSIS_API_KEY must contain 32\+ characters"):
        Settings(
            _env_file=None,
            app_environment="production",
            admin_api_key="a" * 32,
            analysis_api_key="short",
        )

    with pytest.raises(ValueError, match="OPENAI_BASE_URL must use HTTPS"):
        Settings(
            _env_file=None,
            app_environment="production",
            admin_api_key="a" * 32,
            analysis_api_key="b" * 32,
            ai_report_provider="openai",
            openai_api_key="test-openai-key",
            openai_base_url="http://api.example.test/v1",
        )


def test_sensitive_admin_responses_disable_caching_and_add_security_headers():
    app.dependency_overrides[get_settings] = lambda: _settings("test-admin-secret")
    try:
        response = TestClient(app).get(
            "/api/v1/admin/backtests",
            headers={"X-Admin-Key": "test-admin-secret"},
        )
        assert response.headers["Cache-Control"] == "no-store, private"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "camera=()" in response.headers["Permissions-Policy"]
    finally:
        app.dependency_overrides.pop(get_settings, None)
