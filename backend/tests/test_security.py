import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient
from redis.exceptions import RedisError

from app.core.errors import provider_exception_handler
from app.core.rate_limit import (
    RateLimitMiddleware,
    RedisSlidingWindowLimiter,
    SlidingWindowLimiter,
)
from app.providers.errors import ProviderAuthenticationError, ProviderError
from app.core.security import SecurityHeadersMiddleware
from app.core.analysis_access import AnalysisAccessMiddleware


def test_expensive_api_rate_limit_uses_trusted_proxy_client_ip():
    test_app = FastAPI()
    test_app.add_middleware(
        RateLimitMiddleware,
        enabled=True,
        window_seconds=60,
        request_limit=10,
        expensive_request_limit=2,
        trust_proxy_headers=True,
    )

    @test_app.get("/api/v1/stocks/{symbol}/ai-report")
    def report(symbol: str):
        return {"symbol": symbol}

    client = TestClient(test_app)
    headers = {"X-Real-IP": "203.0.113.10"}
    assert client.get("/api/v1/stocks/AAPL/ai-report", headers=headers).status_code == 200
    second = client.get("/api/v1/stocks/AAPL/ai-report", headers=headers)
    blocked = client.get("/api/v1/stocks/AAPL/ai-report", headers=headers)

    assert second.headers["X-RateLimit-Remaining"] == "0"
    assert blocked.status_code == 429
    assert blocked.headers["X-RateLimit-Limit"] == "2"
    assert int(blocked.headers["Retry-After"]) > 0
    assert blocked.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert blocked.json()["data_as_of"]
    assert (
        client.get(
            "/api/v1/stocks/AAPL/ai-report",
            headers={"X-Real-IP": "203.0.113.11"},
        ).status_code
        == 200
    )


def test_walk_forward_backtest_uses_expensive_rate_limit_group():
    test_app = FastAPI()
    test_app.add_middleware(
        RateLimitMiddleware,
        enabled=True,
        window_seconds=60,
        request_limit=10,
        expensive_request_limit=1,
        trust_proxy_headers=False,
    )

    @test_app.post("/api/v1/backtests/walk-forward")
    def validate_backtest():
        return {"status": "experimental"}

    client = TestClient(test_app)
    first = client.post("/api/v1/backtests/walk-forward")
    blocked = client.post("/api/v1/backtests/walk-forward")

    assert first.status_code == 200
    assert first.headers["X-RateLimit-Limit"] == "1"
    assert blocked.status_code == 429
    assert blocked.headers["X-RateLimit-Limit"] == "1"


def test_admin_engine_comparison_uses_expensive_rate_limit_group():
    test_app = FastAPI()
    test_app.add_middleware(
        RateLimitMiddleware,
        enabled=True,
        window_seconds=60,
        request_limit=10,
        expensive_request_limit=1,
        trust_proxy_headers=False,
    )

    @test_app.post("/api/v1/admin/backtests/compare")
    def compare_engines():
        return {"status": "experimental"}

    client = TestClient(test_app)
    first = client.post("/api/v1/admin/backtests/compare")
    blocked = client.post("/api/v1/admin/backtests/compare")

    assert first.status_code == 200
    assert first.headers["X-RateLimit-Limit"] == "1"
    assert blocked.status_code == 429


def test_admin_strategy_comparison_uses_expensive_rate_limit_group():
    test_app = FastAPI()
    test_app.add_middleware(
        RateLimitMiddleware,
        enabled=True,
        window_seconds=60,
        request_limit=10,
        expensive_request_limit=1,
        trust_proxy_headers=False,
    )

    @test_app.post("/api/v1/admin/backtests/strategies/compare")
    def compare_strategies():
        return {"status": "experimental"}

    client = TestClient(test_app)
    first = client.post("/api/v1/admin/backtests/strategies/compare")
    blocked = client.post("/api/v1/admin/backtests/strategies/compare")

    assert first.status_code == 200
    assert first.headers["X-RateLimit-Limit"] == "1"
    assert blocked.status_code == 429


def test_manual_ingestion_uses_expensive_rate_limit_group():
    test_app = FastAPI()
    test_app.add_middleware(
        RateLimitMiddleware,
        enabled=True,
        window_seconds=60,
        request_limit=10,
        expensive_request_limit=1,
        trust_proxy_headers=False,
    )

    @test_app.post("/api/v1/admin/ingestion/{symbol}")
    def ingest(symbol: str):
        return {"symbol": symbol}

    client = TestClient(test_app)
    first = client.post("/api/v1/admin/ingestion/AAPL")
    blocked = client.post("/api/v1/admin/ingestion/AAPL")

    assert first.status_code == 200
    assert first.headers["X-RateLimit-Limit"] == "1"
    assert blocked.status_code == 429


def test_corporate_action_ingestion_uses_expensive_rate_limit_group():
    test_app = FastAPI()
    test_app.add_middleware(
        RateLimitMiddleware,
        enabled=True,
        window_seconds=60,
        request_limit=10,
        expensive_request_limit=1,
        trust_proxy_headers=False,
    )

    @test_app.post("/api/v1/admin/corporate-actions/ingestion/{source}/{symbol}")
    def ingest_actions(source: str, symbol: str):
        return {"source": source, "symbol": symbol}

    client = TestClient(test_app)
    first = client.post("/api/v1/admin/corporate-actions/ingestion/test/005930")
    blocked = client.post("/api/v1/admin/corporate-actions/ingestion/test/005930")

    assert first.status_code == 200
    assert first.headers["X-RateLimit-Limit"] == "1"
    assert blocked.status_code == 429


def test_corporate_action_candidate_preview_uses_expensive_rate_limit_group():
    test_app = FastAPI()
    test_app.add_middleware(
        RateLimitMiddleware,
        enabled=True,
        window_seconds=60,
        request_limit=10,
        expensive_request_limit=1,
        trust_proxy_headers=False,
    )

    @test_app.get("/api/v1/admin/corporate-actions/candidates/{source}/{symbol}")
    def candidates(source: str, symbol: str):
        return {"source": source, "symbol": symbol}

    client = TestClient(test_app)
    first = client.get("/api/v1/admin/corporate-actions/candidates/dart/005930")
    blocked = client.get("/api/v1/admin/corporate-actions/candidates/dart/005930")

    assert first.status_code == 200
    assert first.headers["X-RateLimit-Limit"] == "1"
    assert blocked.status_code == 429


def test_corporate_action_approval_uses_expensive_rate_limit_group():
    test_app = FastAPI()
    test_app.add_middleware(
        RateLimitMiddleware,
        enabled=True,
        window_seconds=60,
        request_limit=10,
        expensive_request_limit=1,
        trust_proxy_headers=False,
    )

    @test_app.post("/api/v1/admin/corporate-actions/approvals/{source}/{symbol}")
    def approve(source: str, symbol: str):
        return {"source": source, "symbol": symbol}

    path = "/api/v1/admin/corporate-actions/approvals/dart/005930"
    client = TestClient(test_app)
    assert client.post(path).status_code == 200
    assert client.post(path).status_code == 429


def test_model_promotion_uses_expensive_rate_limit_group():
    test_app = FastAPI()
    test_app.add_middleware(
        RateLimitMiddleware,
        enabled=True,
        window_seconds=60,
        request_limit=10,
        expensive_request_limit=1,
        trust_proxy_headers=False,
    )

    @test_app.post("/api/v1/admin/models/xgb-test/promote")
    def promote():
        return {"status": "experimental"}

    client = TestClient(test_app)
    assert client.post("/api/v1/admin/models/xgb-test/promote").status_code == 200
    assert client.post("/api/v1/admin/models/xgb-test/promote").status_code == 429


def test_sliding_window_limiter_bounds_untrusted_client_keys_and_expires_attempts():
    now = [100.0]
    limiter = SlidingWindowLimiter(max_keys=3, clock=lambda: now[0])

    for client in ("client-1", "client-2", "client-3", "client-4"):
        assert limiter.consume(client, limit=1, window=60)[0] is True

    assert limiter.key_count == 3
    # client-1 was the least-recently-used entry and was evicted at capacity.
    assert limiter.consume("client-1", limit=1, window=60)[0] is True
    assert limiter.consume("client-1", limit=1, window=60)[0] is False

    now[0] += 61
    assert limiter.is_limited("client-1", limit=1, window=60) is False


def test_redis_limiter_uses_atomic_script_and_hashes_client_key():
    class FakeRedis:
        def __init__(self):
            self.arguments = []
            self.deleted = []
            self.results = [[1, 2, 0], 1]

        async def eval(self, *arguments):
            self.arguments.append(arguments)
            return self.results.pop(0)

        async def delete(self, key):
            self.deleted.append(key)

    client = FakeRedis()
    limiter = RedisSlidingWindowLimiter(client=client, clock=lambda: 100.0)
    result = asyncio.run(limiter.consume("general:203.0.113.9", limit=3, window=60))
    limited = asyncio.run(limiter.is_limited("general:203.0.113.9", limit=3, window=60))
    asyncio.run(limiter.clear("general:203.0.113.9"))

    assert result == (True, 2, 0)
    assert limited is True
    assert client.arguments[0][1] == 1
    assert client.arguments[0][2].startswith("stockpilot:rate-limit:")
    assert "203.0.113.9" not in client.arguments[0][2]
    assert client.arguments[0][3:6] == (100.0, 60, 3)
    assert client.arguments[0][2] == client.arguments[1][2] == client.deleted[0]


def test_distributed_rate_limit_fails_closed_when_redis_is_unavailable():
    class UnavailableLimiter:
        async def consume(self, key: str, *, limit: int, window: int):
            raise RedisError("secret redis endpoint")

    test_app = FastAPI()
    test_app.add_middleware(
        RateLimitMiddleware,
        enabled=True,
        window_seconds=60,
        request_limit=10,
        expensive_request_limit=1,
        trust_proxy_headers=False,
        backend="redis",
        distributed_limiter=UnavailableLimiter(),
    )

    @test_app.get("/api/v1/test")
    def endpoint():
        return {"ok": True}

    response = TestClient(test_app).get("/api/v1/test")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "RATE_LIMIT_UNAVAILABLE"
    assert response.headers["Retry-After"] == "1"
    assert "secret redis endpoint" not in response.text


def test_provider_error_response_redacts_credentials_and_account_identifiers():
    test_app = FastAPI()
    test_app.add_exception_handler(ProviderError, provider_exception_handler)

    @test_app.get("/provider-failure")
    def provider_failure():
        raise ProviderAuthenticationError(
            "authentication failed with Bearer top-secret-token",
            code="provider-authentication-failed",
            request_id="provider-request-123",
            data={
                "access_token": "top-secret-token",
                "nested": {
                    "accountNo": "123-456-789",
                    "hint": "renew credentials",
                },
            },
        )

    response = TestClient(test_app).get("/provider-failure")
    payload = response.json()
    serialized = response.text

    assert response.status_code == 502
    assert payload["error"]["message"] == "외부 데이터 제공자의 인증에 실패했습니다."
    assert payload["error"]["data"]["access_token"] == "[REDACTED]"
    assert payload["error"]["data"]["nested"]["accountNo"] == "[REDACTED]"
    assert payload["error"]["data"]["nested"]["hint"] == "renew credentials"
    assert payload["error"]["data"]["provider_request_id"] == "provider-request-123"
    assert "top-secret-token" not in serialized
    assert "123-456-789" not in serialized


def test_provider_error_response_and_log_reject_untrusted_error_codes(caplog):
    test_app = FastAPI()
    test_app.add_exception_handler(ProviderError, provider_exception_handler)

    @test_app.get("/provider-untrusted-code")
    def provider_failure():
        raise ProviderAuthenticationError(
            "authentication failed",
            code="access_token=top-secret-token",
        )

    with caplog.at_level("WARNING"):
        response = TestClient(test_app).get("/provider-untrusted-code")

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "provider-error"
    assert "top-secret-token" not in response.text
    assert "top-secret-token" not in caplog.text


def test_api_security_headers_include_restrictive_csp():
    test_app = FastAPI()
    test_app.add_middleware(SecurityHeadersMiddleware)

    @test_app.get("/test")
    def endpoint():
        return {"ok": True}

    response = TestClient(test_app).get("/test")

    assert response.status_code == 200
    assert "default-src 'none'" in response.headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_api_documentation_csp_allows_only_required_documentation_assets():
    test_app = FastAPI()
    test_app.add_middleware(SecurityHeadersMiddleware)
    response = TestClient(test_app).get("/docs")

    assert response.status_code == 200
    policy = response.headers["Content-Security-Policy"]
    assert "script-src 'self' https://cdn.jsdelivr.net" in policy
    assert "frame-ancestors 'none'" in policy
    assert "'unsafe-eval'" not in policy


def test_analysis_access_key_protects_only_costly_public_endpoints():
    test_app = FastAPI()
    test_app.add_middleware(AnalysisAccessMiddleware, api_key="bounded-analysis-secret")

    @test_app.get("/api/v1/stocks/{symbol}/quote")
    def quote(symbol: str):
        return {"symbol": symbol}

    @test_app.get("/api/v1/stocks/{symbol}/ai-report")
    def report(symbol: str):
        return {"symbol": symbol}

    @test_app.get("/api/v1/admin/models")
    def admin_models():
        return {"ok": True}

    client = TestClient(test_app)
    assert client.get("/api/v1/stocks/AAPL/quote").status_code == 200
    assert client.get("/api/v1/admin/models").status_code == 200
    rejected = client.get("/api/v1/stocks/AAPL/ai-report")
    accepted = client.get(
        "/api/v1/stocks/AAPL/ai-report",
        headers={"X-Analysis-Key": "bounded-analysis-secret"},
    )

    assert rejected.status_code == 401
    assert rejected.json()["error"]["code"] == "ANALYSIS_AUTHENTICATION_REQUIRED"
    assert "bounded-analysis-secret" not in rejected.text
    assert accepted.status_code == 200


def test_analysis_access_key_protects_public_backtest_posts():
    test_app = FastAPI()
    test_app.add_middleware(AnalysisAccessMiddleware, api_key="bounded-analysis-secret")

    @test_app.post("/api/v1/backtests")
    def backtest():
        return {"ok": True}

    client = TestClient(test_app)
    assert client.post("/api/v1/backtests").status_code == 401
    assert client.post(
        "/api/v1/backtests",
        headers={"X-Analysis-Key": "bounded-analysis-secret"},
    ).status_code == 200
