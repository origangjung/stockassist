import asyncio
import json

import structlog
from fastapi.testclient import TestClient
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.config import Settings
from app.main import app
from app.observability import DependencySpec, HealthService
from app.observability.health import build_health_service
from app.observability.logging import configure_logging
from app.observability.sentry import configure_sentry, scrub_sensitive_data


def test_readiness_reports_required_dependency_failure_without_error_details():
    async def healthy() -> None:
        return None

    async def failed() -> None:
        raise ConnectionError("secret connection details")

    service = HealthService(
        [
            DependencySpec("database", True, healthy),
            DependencySpec("redis", True, failed),
            DependencySpec("optional", False, None),
        ]
    )
    ready, payload = asyncio.run(service.readiness())
    checks = payload["checks"]

    assert ready is False
    assert payload["status"] == "not_ready"
    assert checks["database"]["status"] == "up"
    assert checks["redis"]["status"] == "down"
    assert checks["redis"]["error_type"] == "ConnectionError"
    assert "secret connection details" not in str(payload)
    assert checks["optional"]["status"] == "disabled"


def test_readiness_times_out_slow_required_dependency():
    async def slow() -> None:
        await asyncio.sleep(0.05)

    service = HealthService(
        [DependencySpec("database", True, slow)],
        timeout_seconds=0.001,
    )
    ready, payload = asyncio.run(service.readiness())
    assert ready is False
    assert payload["checks"]["database"]["error_type"] == "TimeoutError"


def test_redis_is_required_when_distributed_rate_limit_is_enabled():
    service = build_health_service(
        Settings(_env_file=None, realtime_enabled=False, rate_limit_backend="redis"),
        sessions=None,
    )
    redis = next(item for item in service._dependencies if item.name == "redis")

    assert redis.required is True


def test_health_and_prometheus_endpoints_are_exposed():
    client = TestClient(app)
    live = client.get("/health/live")
    ready = client.get("/health/ready")
    metrics = client.get("/metrics/")

    assert live.status_code == 200
    assert live.json()["status"] == "alive"
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
    assert metrics.status_code == 200
    assert "stockpilot_http_requests_total" in metrics.text
    assert "stockpilot_http_request_duration_seconds" in metrics.text
    assert "stockpilot_dependency_ready" in metrics.text


def test_structured_log_contains_context_without_request_payload(capsys):
    configure_logging("INFO", "json")
    clear_contextvars()
    bind_contextvars(request_id="log-test-id")
    structlog.get_logger("test").info(
        "safe_event",
        route="/stocks/{symbol}",
        status=200,
    )
    clear_contextvars()

    payload = json.loads(capsys.readouterr().err.strip().splitlines()[-1])
    assert payload["event"] == "safe_event"
    assert payload["request_id"] == "log-test-id"
    assert payload["route"] == "/stocks/{symbol}"
    assert "authorization" not in payload
    assert "body" not in payload


def test_sentry_is_optional_and_uses_privacy_safe_defaults(monkeypatch):
    captured = {}

    def fake_init(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("app.observability.sentry.sentry_sdk.init", fake_init)
    disabled = configure_sentry(Settings(_env_file=None, sentry_dsn=None))
    enabled = configure_sentry(
        Settings(
            _env_file=None,
            sentry_dsn="https://public@example.invalid/1",
            sentry_traces_sample_rate=0.1,
        )
    )

    assert disabled is False
    assert enabled is True
    assert captured["send_default_pii"] is False
    assert captured["include_local_variables"] is False
    assert captured["max_request_body_size"] == "never"
    assert captured["traces_sample_rate"] == 0.1


def test_sentry_scrubber_removes_body_and_sensitive_headers():
    event = {
        "request": {
            "data": {"secret": "value"},
            "headers": {
                "Authorization": "Bearer secret",
                "X-Admin-Key": "admin-secret",
                "Accept": "application/json",
            },
        }
    }
    scrubbed = scrub_sensitive_data(event, {})
    request = scrubbed["request"]
    assert "data" not in request
    assert request["headers"]["Authorization"] == "[Filtered]"
    assert request["headers"]["X-Admin-Key"] == "[Filtered]"
    assert request["headers"]["Accept"] == "application/json"
