from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from threading import Lock
import time
from typing import Iterator, Protocol

import httpx2
from redis import Redis
from redis.exceptions import RedisError

from app.providers.errors import ProviderAuthenticationError, ProviderUnavailableError
from app.providers.toss.rate_limit import TossRateLimiter


@dataclass(frozen=True)
class AccessToken:
    value: str
    expires_at: float


class TokenCache(Protocol):
    def get(self, key: str) -> AccessToken | None: ...

    def set(self, key: str, token: AccessToken) -> None: ...

    def delete(self, key: str, expected_value: str | None = None) -> None: ...

    def issue_lock(self, key: str) -> AbstractContextManager[None]: ...


class InMemoryTokenCache:
    def __init__(self) -> None:
        self._tokens: dict[str, AccessToken] = {}

    def get(self, key: str) -> AccessToken | None:
        return self._tokens.get(key)

    def set(self, key: str, token: AccessToken) -> None:
        self._tokens[key] = token

    def delete(self, key: str, expected_value: str | None = None) -> None:
        current = self._tokens.get(key)
        if expected_value is None or (current and current.value == expected_value):
            self._tokens.pop(key, None)

    @contextmanager
    def issue_lock(self, key: str) -> Iterator[None]:
        del key
        yield


class RedisTokenCache:
    """Redis TTL cache with a process-local fallback for transient Redis outages."""

    def __init__(self, redis_url: str, *, clock=time.time) -> None:
        self._redis = Redis.from_url(redis_url, decode_responses=True)
        self._fallback = InMemoryTokenCache()
        self._clock = clock

    def get(self, key: str) -> AccessToken | None:
        try:
            value = self._redis.get(key)
            ttl = self._redis.ttl(key) if value is not None else -2
        except RedisError:
            return self._fallback.get(key)
        if value is None or ttl <= 0:
            return self._fallback.get(key)
        token = AccessToken(value=value, expires_at=self._clock() + ttl)
        self._fallback.set(key, token)
        return token

    def set(self, key: str, token: AccessToken) -> None:
        self._fallback.set(key, token)
        ttl = max(1, int(token.expires_at - self._clock()))
        try:
            self._redis.set(key, token.value, ex=ttl)
        except RedisError:
            pass

    def delete(self, key: str, expected_value: str | None = None) -> None:
        self._fallback.delete(key, expected_value)
        try:
            if expected_value is None:
                self._redis.delete(key)
            else:
                self._redis.eval(
                    "if redis.call('get', KEYS[1]) == ARGV[1] then "
                    "return redis.call('del', KEYS[1]) else return 0 end",
                    1,
                    key,
                    expected_value,
                )
        except RedisError:
            pass

    @contextmanager
    def issue_lock(self, key: str) -> Iterator[None]:
        lock = self._redis.lock(f"{key}:issue-lock", timeout=15, blocking_timeout=10)
        try:
            acquired = lock.acquire(blocking=True)
        except RedisError:
            yield
            return
        if not acquired:
            raise ProviderUnavailableError(
                "Timed out waiting for the shared Toss OAuth token lock",
                code="oauth-lock-timeout",
            )
        try:
            yield
        finally:
            try:
                lock.release()
            except RedisError:
                pass


class TossTokenManager:
    def __init__(
        self,
        client: httpx2.Client,
        limiter: TossRateLimiter,
        *,
        client_id: str,
        client_secret: str,
        cache: TokenCache | None = None,
        clock=time.time,
    ) -> None:
        self._client = client
        self._limiter = limiter
        self._client_id = client_id
        self._client_secret = client_secret
        self._cache = cache or InMemoryTokenCache()
        self._clock = clock
        self._lock = Lock()
        self._cache_key = f"toss:oauth:{client_id}"

    def get(self) -> str:
        token = self._cache.get(self._cache_key)
        if self._usable(token):
            return token.value
        with self._lock:
            with self._cache.issue_lock(self._cache_key):
                token = self._cache.get(self._cache_key)
                if self._usable(token):
                    return token.value
                return self._issue().value

    def invalidate(self, expected_token: str | None = None) -> None:
        self._cache.delete(self._cache_key, expected_token)

    def _usable(self, token: AccessToken | None) -> bool:
        return token is not None and token.expires_at - 30 > self._clock()

    def _issue(self) -> AccessToken:
        self._limiter.acquire("AUTH")
        try:
            response = self._client.post(
                "/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
            )
        except httpx2.RequestError as exc:
            raise ProviderUnavailableError("Toss OAuth server is unavailable") from exc
        self._limiter.observe("AUTH", response.headers)
        payload = _json_object(response)
        if response.status_code >= 400:
            raise ProviderAuthenticationError(
                payload.get("error_description") or "Toss OAuth authentication failed",
                code=str(payload.get("error") or "oauth-error"),
                status_code=502,
            )
        try:
            value = str(payload["access_token"])
            expires_in = int(payload["expires_in"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderAuthenticationError(
                "Toss OAuth response did not contain a valid access token",
                code="invalid-oauth-response",
            ) from exc
        token = AccessToken(value=value, expires_at=self._clock() + expires_in)
        self._cache.set(self._cache_key, token)
        return token


def _json_object(response: httpx2.Response) -> dict:
    try:
        payload = response.json()
    except ValueError as exc:
        raise ProviderUnavailableError("Toss returned a non-JSON response") from exc
    if not isinstance(payload, dict):
        raise ProviderUnavailableError("Toss returned an invalid response envelope")
    return payload
