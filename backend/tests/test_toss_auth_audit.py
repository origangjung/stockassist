import httpx2
import pytest

from app.providers.audit import ProviderAuditEvent
from app.providers.errors import ProviderAuthenticationError, ProviderUnavailableError
from app.providers.toss.auth import TossTokenManager
from app.providers.toss.provider import TossProvider
from app.providers.toss.rate_limit import TossRateLimiter


BASE_URL = "https://openapi.tossinvest.com"
CLIENT_ID = "audit-client-id"
CLIENT_SECRET = "sensitive-client-secret"
ACCESS_TOKEN = "very-sensitive-access-token"


class _AuditSink:
    def __init__(self) -> None:
        self.events: list[ProviderAuditEvent] = []

    def save(self, event: ProviderAuditEvent) -> None:
        self.events.append(event)


class _FailingAuditSink:
    def save(self, event: ProviderAuditEvent) -> None:
        del event
        raise RuntimeError("audit storage unavailable")


def _manager(
    transport: httpx2.MockTransport,
    audit_sink: _AuditSink | _FailingAuditSink,
) -> tuple[httpx2.Client, TossTokenManager]:
    http = httpx2.Client(base_url=BASE_URL, transport=transport)
    return (
        http,
        TossTokenManager(
            http,
            TossRateLimiter(),
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            audit_sink=audit_sink,
        ),
    )


def test_auth_audit_records_only_network_issuance_and_never_secrets():
    sink = _AuditSink()
    calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        assert request.url.path == "/oauth2/token"
        return httpx2.Response(
            200,
            headers={"X-Request-Id": "oauth-success"},
            json={"access_token": ACCESS_TOKEN, "expires_in": 3600},
        )

    http, tokens = _manager(httpx2.MockTransport(handler), sink)
    try:
        assert tokens.get() == ACCESS_TOKEN
        assert tokens.get() == ACCESS_TOKEN
    finally:
        http.close()

    assert calls == 1
    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.provider == "toss"
    assert event.method == "POST"
    assert event.endpoint == "/oauth2/token"
    assert event.api_group == "AUTH"
    assert event.outcome == "success"
    assert event.status_code == 200
    assert event.error_code is None
    assert event.provider_request_id == "oauth-success"
    assert event.attempt_count == 1
    assert event.duration_ms >= 0
    serialized = repr(event)
    assert CLIENT_ID not in serialized
    assert CLIENT_SECRET not in serialized
    assert ACCESS_TOKEN not in serialized


def test_auth_audit_records_http_auth_failure_without_error_description():
    sink = _AuditSink()

    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.path == "/oauth2/token"
        return httpx2.Response(
            401,
            json={
                "error": "invalid_client",
                "error_description": "do not persist this diagnostic",
                "requestId": "oauth-denied",
            },
        )

    http, tokens = _manager(httpx2.MockTransport(handler), sink)
    try:
        with pytest.raises(ProviderAuthenticationError) as caught:
            tokens.get()
    finally:
        http.close()

    assert caught.value.code == "toss-oauth-http-401"
    assert caught.value.request_id == "oauth-denied"
    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.outcome == "error"
    assert event.status_code == 401
    assert event.error_code == "toss-oauth-http-401"
    assert event.provider_request_id == "oauth-denied"
    serialized = repr(event)
    assert "do not persist this diagnostic" not in serialized
    assert CLIENT_SECRET not in serialized


def test_auth_audit_records_invalid_oauth_envelope():
    sink = _AuditSink()

    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.path == "/oauth2/token"
        return httpx2.Response(200, headers={"X-Request-Id": "oauth-invalid"}, json=[])

    http, tokens = _manager(httpx2.MockTransport(handler), sink)
    try:
        with pytest.raises(ProviderUnavailableError) as caught:
            tokens.get()
    finally:
        http.close()

    assert caught.value.code == "invalid-oauth-response"
    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.outcome == "error"
    assert event.status_code == 200
    assert event.error_code == "invalid-oauth-response"
    assert event.provider_request_id == "oauth-invalid"


@pytest.mark.parametrize(
    "payload",
    [
        {"access_token": None, "expires_in": 3600},
        {"access_token": "", "expires_in": 3600},
        {"access_token": "valid-looking-token", "expires_in": 30},
    ],
)
def test_auth_rejects_unusable_tokens_without_recording_success(payload: dict):
    sink = _AuditSink()

    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.path == "/oauth2/token"
        return httpx2.Response(200, headers={"X-Request-Id": "oauth-unusable"}, json=payload)

    http, tokens = _manager(httpx2.MockTransport(handler), sink)
    try:
        with pytest.raises(ProviderAuthenticationError) as caught:
            tokens.get()
    finally:
        http.close()

    assert caught.value.code == "invalid-oauth-response"
    assert len(sink.events) == 1
    assert sink.events[0].outcome == "error"
    assert sink.events[0].error_code == "invalid-oauth-response"
    assert sink.events[0].provider_request_id == "oauth-unusable"


def test_auth_audit_records_transport_failure():
    sink = _AuditSink()

    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("network unavailable", request=request)

    http, tokens = _manager(httpx2.MockTransport(handler), sink)
    try:
        with pytest.raises(ProviderUnavailableError):
            tokens.get()
    finally:
        http.close()

    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.outcome == "transport_error"
    assert event.status_code is None
    assert event.error_code == "provider-unavailable"
    assert event.provider_request_id is None


def test_auth_audit_storage_failure_does_not_block_token_issue():
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.path == "/oauth2/token"
        return httpx2.Response(200, json={"access_token": ACCESS_TOKEN, "expires_in": 3600})

    http, tokens = _manager(httpx2.MockTransport(handler), _FailingAuditSink())
    try:
        assert tokens.get() == ACCESS_TOKEN
    finally:
        http.close()


def test_toss_provider_factory_wires_the_audit_sink_to_oauth_issuance():
    sink = _AuditSink()

    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path == "/oauth2/token":
            return httpx2.Response(200, json={"access_token": ACCESS_TOKEN, "expires_in": 3600})
        if request.url.path == "/api/v1/prices":
            return httpx2.Response(
                200,
                json={
                    "result": [
                        {
                            "symbol": "005930",
                            "timestamp": "2026-07-23T09:00:00+09:00",
                            "lastPrice": "70000",
                            "currency": "KRW",
                        }
                    ]
                },
            )
        if request.url.path == "/api/v1/stocks":
            return httpx2.Response(
                200,
                json={
                    "result": [
                        {
                            "symbol": "005930",
                            "name": "Samsung Electronics",
                            "market": "KOSPI",
                            "currency": "KRW",
                            "listDate": "1975-06-11",
                        }
                    ]
                },
            )
        raise AssertionError(f"unexpected path: {request.url.path}")

    provider = TossProvider.create(
        base_url=BASE_URL,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        transport=httpx2.MockTransport(handler),
        audit_sink=sink,
    )
    try:
        assert provider.get_quote("005930").price == 70000
    finally:
        provider.close()

    auth_events = [event for event in sink.events if event.api_group == "AUTH"]
    assert len(auth_events) == 1
    assert auth_events[0].endpoint == "/oauth2/token"
