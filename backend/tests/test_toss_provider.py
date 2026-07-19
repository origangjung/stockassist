from datetime import date
from decimal import Decimal

import httpx2
import pytest

from app.providers.errors import ProviderNotFoundError
from app.providers.audit import ProviderAuditEvent
from app.providers.toss.auth import TossTokenManager
from app.providers.toss.client import TossApiClient
from app.providers.toss.provider import TossProvider
from app.providers.toss.rate_limit import TossRateLimiter


BASE_URL = "https://openapi.tossinvest.com"


class _AuditSink:
    def __init__(self) -> None:
        self.events: list[ProviderAuditEvent] = []

    def save(self, event: ProviderAuditEvent) -> None:
        self.events.append(event)


def _token_response() -> httpx2.Response:
    return httpx2.Response(
        200,
        json={"access_token": "access-token", "token_type": "Bearer", "expires_in": 86400},
    )


def _stock_response() -> httpx2.Response:
    return httpx2.Response(
        200,
        json={
            "result": [
                {
                    "symbol": "005930",
                    "name": "삼성전자",
                    "englishName": "Samsung Electronics",
                    "isinCode": "KR7005930003",
                    "market": "KOSPI",
                    "securityType": "STOCK",
                    "isCommonShare": True,
                    "status": "ACTIVE",
                    "currency": "KRW",
                    "sharesOutstanding": "5969782550",
                    "listDate": "1975-06-11",
                }
            ]
        },
    )


def test_quote_uses_one_cached_oauth_token_and_preserves_unavailable_fields():
    calls = {"token": 0, "price": 0, "stock": 0}

    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path == "/oauth2/token":
            calls["token"] += 1
            assert b"grant_type=client_credentials" in request.content
            assert b"client_secret=secret" in request.content
            return _token_response()
        assert request.headers["Authorization"] == "Bearer access-token"
        if request.url.path == "/api/v1/prices":
            calls["price"] += 1
            assert request.url.params["symbols"] == "005930"
            return httpx2.Response(
                200,
                json={
                    "result": [
                        {
                            "symbol": "005930",
                            "timestamp": "2026-07-13T09:30:00+09:00",
                            "lastPrice": "72100",
                            "currency": "KRW",
                        }
                    ]
                },
            )
        if request.url.path == "/api/v1/stocks":
            calls["stock"] += 1
            return _stock_response()
        raise AssertionError(f"unexpected path: {request.url.path}")

    provider = TossProvider.create(
        base_url=BASE_URL,
        client_id="client",
        client_secret="secret",
        transport=httpx2.MockTransport(handler),
    )
    try:
        first = provider.get_quote("005930")
        second = provider.get_quote("005930")
    finally:
        provider.close()

    assert first.price == Decimal("72100")
    assert first.name == "삼성전자"
    assert first.change is first.change_percent is first.volume is None
    assert second.price == first.price
    assert calls == {"token": 1, "price": 2, "stock": 1}


def test_candle_pagination_and_market_data_shapes_are_mapped():
    candle_calls: list[str | None] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path == "/oauth2/token":
            return _token_response()
        if request.url.path == "/api/v1/candles":
            before = request.url.params.get("before")
            candle_calls.append(before)
            timestamp = (
                "2026-07-13T00:00:00+09:00" if before is None else "2026-07-12T00:00:00+09:00"
            )
            return httpx2.Response(
                200,
                json={
                    "result": {
                        "candles": [
                            {
                                "timestamp": timestamp,
                                "openPrice": "70000",
                                "highPrice": "73000",
                                "lowPrice": "69500",
                                "closePrice": "72100",
                                "volume": "1234567",
                                "currency": "KRW",
                            }
                        ],
                        "nextBefore": "2026-07-12T00:00:00+09:00" if before is None else None,
                    }
                },
            )
        if request.url.path == "/api/v1/orderbook":
            return httpx2.Response(
                200,
                json={
                    "result": {
                        "timestamp": "2026-07-13T09:30:00+09:00",
                        "currency": "KRW",
                        "asks": [{"price": "72200", "volume": "100"}],
                        "bids": [{"price": "72100", "volume": "200"}],
                    }
                },
            )
        if request.url.path == "/api/v1/trades":
            return httpx2.Response(
                200,
                json={
                    "result": [
                        {
                            "price": "72100",
                            "volume": "3",
                            "timestamp": "2026-07-13T09:30:00+09:00",
                            "currency": "KRW",
                        }
                    ]
                },
            )
        raise AssertionError(f"unexpected path: {request.url.path}")

    provider = TossProvider.create(
        base_url=BASE_URL,
        client_id="client",
        client_secret="secret",
        transport=httpx2.MockTransport(handler),
    )
    try:
        candles = provider.get_candles("005930", 2)
        asks, bids = provider.get_orderbook("005930")
        trades = provider.get_trades("005930", 1)
    finally:
        provider.close()

    assert len(candles) == 2
    assert all(candle.price_basis == "provider_adjusted" for candle in candles)
    assert candle_calls == [None, "2026-07-12T00:00:00+09:00"]
    assert asks[0].price == Decimal("72200") and bids[0].quantity == 200
    assert trades[0].side is None and trades[0].quantity == 3


def test_warnings_keep_unknown_types_forward_compatible():
    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path == "/oauth2/token":
            return _token_response()
        return httpx2.Response(
            200,
            json={
                "result": [
                    {
                        "warningType": "FUTURE_WARNING_TYPE",
                        "exchange": None,
                        "startDate": "2026-07-13",
                        "endDate": None,
                    }
                ]
            },
        )

    provider = TossProvider.create(
        base_url=BASE_URL,
        client_id="client",
        client_secret="secret",
        transport=httpx2.MockTransport(handler),
    )
    try:
        warnings = provider.get_warnings("005930")
    finally:
        provider.close()

    assert warnings[0].warning_type == "FUTURE_WARNING_TYPE"
    assert warnings[0].start_date == date(2026, 7, 13)
    assert warnings[0].end_date is None


def test_expired_token_is_reissued_once():
    issued = 0
    price_calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal issued, price_calls
        if request.url.path == "/oauth2/token":
            issued += 1
            return httpx2.Response(
                200,
                json={
                    "access_token": f"token-{issued}",
                    "token_type": "Bearer",
                    "expires_in": 86400,
                },
            )
        if request.url.path == "/api/v1/prices":
            price_calls += 1
            if price_calls == 1:
                return httpx2.Response(
                    401,
                    json={
                        "error": {
                            "requestId": "req-expired",
                            "code": "expired-token",
                            "message": "expired",
                        }
                    },
                )
            return httpx2.Response(200, json={"result": []})
        raise AssertionError(f"unexpected path: {request.url.path}")

    http = httpx2.Client(base_url=BASE_URL, transport=httpx2.MockTransport(handler))
    limiter = TossRateLimiter()
    tokens = TossTokenManager(http, limiter, client_id="client", client_secret="secret")
    client = TossApiClient(http, tokens, limiter, max_retries=0)
    try:
        assert client.get("/api/v1/prices", group="MARKET_DATA") == {"result": []}
    finally:
        client.close()
    assert issued == 2 and price_calls == 2


def test_429_retries_and_terminal_error_preserves_request_id():
    sleeps: list[float] = []
    market_calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal market_calls
        if request.url.path == "/oauth2/token":
            return _token_response()
        market_calls += 1
        if market_calls == 1:
            return httpx2.Response(
                429,
                headers={"Retry-After": "0"},
                json={
                    "error": {
                        "requestId": "req-rate",
                        "code": "rate-limit-exceeded",
                        "message": "slow down",
                    }
                },
            )
        return httpx2.Response(
            404,
            json={
                "error": {
                    "requestId": "req-missing",
                    "code": "stock-not-found",
                    "message": "missing",
                }
            },
        )

    http = httpx2.Client(base_url=BASE_URL, transport=httpx2.MockTransport(handler))
    limiter = TossRateLimiter()
    tokens = TossTokenManager(http, limiter, client_id="client", client_secret="secret")
    client = TossApiClient(http, tokens, limiter, sleep=sleeps.append)
    try:
        with pytest.raises(ProviderNotFoundError) as caught:
            client.get("/api/v1/prices", group="MARKET_DATA")
    finally:
        client.close()

    assert sleeps and sleeps[0] >= 1
    assert caught.value.code == "stock-not-found"
    assert caught.value.request_id == "req-missing"


def test_audit_records_success_request_id_without_request_secrets():
    sink = _AuditSink()

    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path == "/oauth2/token":
            return _token_response()
        return httpx2.Response(
            200,
            headers={"X-Request-Id": "req-success"},
            json={"result": []},
        )

    http = httpx2.Client(base_url=BASE_URL, transport=httpx2.MockTransport(handler))
    limiter = TossRateLimiter()
    tokens = TossTokenManager(http, limiter, client_id="client", client_secret="secret")
    client = TossApiClient(http, tokens, limiter, audit_sink=sink)
    try:
        client.get(
            "/api/v1/prices?not-stored=secret",
            group="MARKET_DATA",
            params={"symbols": "005930", "credential": "not-stored"},
            account_seq=123456,
        )
    finally:
        client.close()

    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.outcome == "success"
    assert event.provider_request_id == "req-success"
    assert event.endpoint == "/api/v1/prices"
    assert event.status_code == 200
    assert event.attempt_count == 1
    serialized = repr(event)
    assert "123456" not in serialized
    assert "credential" not in serialized
    assert "not-stored" not in serialized


def test_audit_records_only_terminal_error_after_retry():
    sink = _AuditSink()
    calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        if request.url.path == "/oauth2/token":
            return _token_response()
        calls += 1
        if calls == 1:
            return httpx2.Response(
                429,
                headers={"Retry-After": "0"},
                json={"error": {"requestId": "req-retry", "code": "rate-limit"}},
            )
        return httpx2.Response(
            404,
            json={"error": {"requestId": "req-terminal", "code": "stock-not-found"}},
        )

    http = httpx2.Client(base_url=BASE_URL, transport=httpx2.MockTransport(handler))
    limiter = TossRateLimiter()
    tokens = TossTokenManager(http, limiter, client_id="client", client_secret="secret")
    client = TossApiClient(http, tokens, limiter, sleep=lambda _: None, audit_sink=sink)
    try:
        with pytest.raises(ProviderNotFoundError):
            client.get("/api/v1/prices", group="MARKET_DATA")
    finally:
        client.close()

    assert len(sink.events) == 1
    assert sink.events[0].outcome == "error"
    assert sink.events[0].provider_request_id == "req-terminal"
    assert sink.events[0].attempt_count == 2
