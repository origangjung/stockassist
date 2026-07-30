from collections import OrderedDict, deque
from collections.abc import Callable
from datetime import datetime, timezone
from hashlib import sha256
from ipaddress import ip_address
from threading import Lock
from time import monotonic, time
from uuid import uuid4

from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.compliance import DISCLAIMER

_EXPENSIVE_SUFFIXES = (
    "/ai-report",
    "/prediction",
    "/score",
    "/financials",
    "/news",
    "/disclosures",
    "/investor-flow",
)
_MAX_CLIENT_IP_HEADER_LENGTH = 64
_MAX_CLIENT_KEY_LENGTH = 64


def client_ip_key(request: Request, *, trust_proxy_headers: bool) -> str:
    """Return a bounded client key, trusting a proxy-provided IP only when enabled.

    Nginx overwrites ``X-Real-IP`` before forwarding a request to the API.  The
    application must still treat that header as untrusted unless the deployment
    explicitly opts in, and must not turn arbitrary header text into an
    unbounded limiter key.
    """

    if trust_proxy_headers:
        real_ip = request.headers.get("X-Real-IP")
        if real_ip is not None and len(real_ip) <= _MAX_CLIENT_IP_HEADER_LENGTH:
            candidate = real_ip.strip()
            if candidate and "%" not in candidate:
                try:
                    return str(ip_address(candidate))
                except ValueError:
                    pass

    client_host = request.client.host if request.client else "unknown"
    return client_host[:_MAX_CLIENT_KEY_LENGTH]

_REDIS_SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window)
local count = redis.call('ZCARD', key)
if count >= limit then
  redis.call('PEXPIRE', key, math.ceil(window * 1000))
  local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
  local retry = 1
  if oldest[2] then
    retry = math.max(1, math.ceil(window - (now - tonumber(oldest[2]))))
  end
  return {0, 0, retry}
end
redis.call('ZADD', key, now, member)
redis.call('PEXPIRE', key, math.ceil(window * 1000))
return {1, limit - count - 1, 0}
"""

_REDIS_LIMIT_STATUS_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window)
local count = redis.call('ZCARD', key)
if count == 0 then
  redis.call('DEL', key)
  return 0
end
redis.call('PEXPIRE', key, math.ceil(window * 1000))
return count >= limit and 1 or 0
"""


class SlidingWindowLimiter:
    """Thread-safe, memory-bounded process-local sliding-window limiter."""

    def __init__(
        self,
        *,
        max_keys: int = 10_000,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if max_keys < 1:
            raise ValueError("max_keys must be positive")
        self._requests: OrderedDict[str, deque[float]] = OrderedDict()
        self._lock = Lock()
        self._max_keys = max_keys
        self._clock = clock
        self._operations = 0

    def consume(self, key: str, *, limit: int, window: int) -> tuple[bool, int, int]:
        if limit < 1 or window < 1:
            raise ValueError("limit and window must be positive")
        now = self._clock()
        with self._lock:
            self._operations += 1
            if self._operations % 256 == 0:
                self._sweep(now - window)
            requests = self._requests.get(key)
            if requests is None:
                if len(self._requests) >= self._max_keys:
                    self._requests.popitem(last=False)
                requests = deque()
                self._requests[key] = requests
            else:
                self._requests.move_to_end(key)
            cutoff = now - window
            self._prune(requests, cutoff)
            if len(requests) >= limit:
                retry_after = max(1, int(window - (now - requests[0])) + 1)
                return False, 0, retry_after
            requests.append(now)
            return True, max(0, limit - len(requests)), 0

    def is_limited(self, key: str, *, limit: int, window: int) -> bool:
        now = self._clock()
        with self._lock:
            requests = self._requests.get(key)
            if requests is None:
                return False
            self._prune(requests, now - window)
            if not requests:
                self._requests.pop(key, None)
                return False
            self._requests.move_to_end(key)
            return len(requests) >= limit

    def clear(self, key: str | None = None) -> None:
        with self._lock:
            if key is None:
                self._requests.clear()
            else:
                self._requests.pop(key, None)

    @property
    def key_count(self) -> int:
        with self._lock:
            return len(self._requests)

    @staticmethod
    def _prune(requests: deque[float], cutoff: float) -> None:
        while requests and requests[0] <= cutoff:
            requests.popleft()

    def _sweep(self, cutoff: float) -> None:
        for key, requests in list(self._requests.items()):
            self._prune(requests, cutoff)
            if not requests:
                self._requests.pop(key, None)


class RedisSlidingWindowLimiter:
    """Atomic sliding-window limiter shared by every API replica."""

    def __init__(
        self,
        redis_url: str | None = None,
        *,
        client: Redis | None = None,
        clock: Callable[[], float] = time,
    ) -> None:
        if client is None and not redis_url:
            raise ValueError("redis_url or client is required")
        self._redis = client or Redis.from_url(redis_url, decode_responses=True)
        self._clock = clock

    async def consume(self, key: str, *, limit: int, window: int) -> tuple[bool, int, int]:
        if limit < 1 or window < 1:
            raise ValueError("limit and window must be positive")
        result = await self._redis.eval(
            _REDIS_SLIDING_WINDOW_SCRIPT,
            1,
            self._key(key),
            self._clock(),
            window,
            limit,
            uuid4().hex,
        )
        allowed, remaining, retry_after = (int(value) for value in result)
        return bool(allowed), remaining, retry_after

    async def is_limited(self, key: str, *, limit: int, window: int) -> bool:
        if limit < 1 or window < 1:
            raise ValueError("limit and window must be positive")
        result = await self._redis.eval(
            _REDIS_LIMIT_STATUS_SCRIPT,
            1,
            self._key(key),
            self._clock(),
            window,
            limit,
        )
        return bool(int(result))

    async def clear(self, key: str) -> None:
        await self._redis.delete(self._key(key))

    async def aclose(self) -> None:
        await self._redis.aclose()

    @staticmethod
    def _key(key: str) -> str:
        digest = sha256(key.encode("utf-8")).hexdigest()
        return f"stockpilot:rate-limit:{digest}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        enabled: bool,
        window_seconds: int,
        request_limit: int,
        expensive_request_limit: int,
        trust_proxy_headers: bool,
        backend: str = "memory",
        redis_url: str | None = None,
        distributed_limiter: RedisSlidingWindowLimiter | None = None,
    ) -> None:
        super().__init__(app)
        self._enabled = enabled
        self._window = window_seconds
        self._request_limit = request_limit
        self._expensive_limit = expensive_request_limit
        self._trust_proxy_headers = trust_proxy_headers
        self._limiter = SlidingWindowLimiter()
        if backend not in {"memory", "redis"}:
            raise ValueError("rate-limit backend must be memory or redis")
        self._distributed_limiter = (
            distributed_limiter
            if backend == "redis" and distributed_limiter is not None
            else RedisSlidingWindowLimiter(redis_url)
            if backend == "redis"
            else None
        )

    async def dispatch(self, request: Request, call_next):
        if not self._enabled or not request.url.path.startswith("/api/"):
            return await call_next(request)
        group = "expensive" if _is_expensive(request) else "general"
        limit = self._expensive_limit if group == "expensive" else self._request_limit
        client = self._client_key(request)
        limiter_key = f"{group}:{client}"
        try:
            if self._distributed_limiter is not None:
                allowed, remaining, retry_after = await self._distributed_limiter.consume(
                    limiter_key,
                    limit=limit,
                    window=self._window,
                )
            else:
                allowed, remaining, retry_after = self._limiter.consume(
                    limiter_key,
                    limit=limit,
                    window=self._window,
                )
        except RedisError:
            return self._error_response(
                request,
                status_code=503,
                code="RATE_LIMIT_UNAVAILABLE",
                message="요청 제한 저장소를 사용할 수 없습니다.",
                headers={"Retry-After": "1"},
            )
        if not allowed:
            return self._error_response(
                request,
                status_code=429,
                code="RATE_LIMIT_EXCEEDED",
                message="요청 한도를 초과했습니다. 잠시 후 다시 시도하세요.",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    def _client_key(self, request: Request) -> str:
        return client_ip_key(request, trust_proxy_headers=self._trust_proxy_headers)

    @staticmethod
    def _error_response(
        request: Request,
        *,
        status_code: int,
        code: str,
        message: str,
        headers: dict[str, str],
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid4()))
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "request_id": request_id,
                "error": {"code": code, "message": message, "data": None},
                "data_as_of": datetime.now(timezone.utc).isoformat(),
                "disclaimer": DISCLAIMER,
                "is_investment_advice": False,
            },
            headers=headers,
        )


def _is_expensive(request: Request) -> bool:
    path = request.url.path.rstrip("/")
    expensive_posts = {
        "/api/v1/backtests",
        "/api/v1/backtests/walk-forward",
        "/api/v1/admin/backtests/compare",
        "/api/v1/admin/backtests/strategies/compare",
    }
    expensive_ingestion = request.method == "POST" and path.startswith("/api/v1/admin/ingestion/")
    expensive_corporate_action_ingestion = request.method == "POST" and path.startswith(
        "/api/v1/admin/corporate-actions/ingestion/"
    )
    expensive_corporate_action_candidates = request.method == "GET" and path.startswith(
        "/api/v1/admin/corporate-actions/candidates/"
    )
    expensive_corporate_action_approval = request.method == "POST" and path.startswith(
        "/api/v1/admin/corporate-actions/approvals/"
    )
    expensive_model_promotion = (
        request.method == "POST"
        and path.startswith("/api/v1/admin/models/")
        and path.endswith("/promote")
    )
    return (
        (request.method == "POST" and path in expensive_posts)
        or expensive_ingestion
        or expensive_corporate_action_ingestion
        or expensive_corporate_action_candidates
        or expensive_corporate_action_approval
        or expensive_model_promotion
        or path.endswith(_EXPENSIVE_SUFFIXES)
    )
