from dataclasses import dataclass
from datetime import datetime
from threading import Lock
import random
import time
from typing import Callable, Mapping
from zoneinfo import ZoneInfo


DEFAULT_GROUP_LIMITS: dict[str, float] = {
    "AUTH": 5,
    "ACCOUNT": 1,
    "ASSET": 5,
    "STOCK": 5,
    "MARKET_INFO": 3,
    "MARKET_DATA": 10,
    "MARKET_DATA_CHART": 5,
    "ORDER": 6,
    "CONDITIONAL_ORDER": 5,
}


@dataclass
class _Bucket:
    rate: float
    capacity: float
    tokens: float
    updated_at: float


class TossRateLimiter:
    """Process-local token buckets, dynamically tightened by Toss response headers."""

    def __init__(
        self,
        limits: Mapping[str, float] | None = None,
        *,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._clock = monotonic
        self._sleep = sleep
        now = monotonic()
        self._buckets = {
            group: _Bucket(rate, rate, rate, now)
            for group, rate in (limits or DEFAULT_GROUP_LIMITS).items()
        }
        self._lock = Lock()

    def acquire(self, group: str) -> None:
        while True:
            with self._lock:
                bucket = self._bucket(group)
                now = self._clock()
                effective_rate = self.effective_rate(group)
                effective_capacity = effective_rate
                elapsed = max(0.0, now - bucket.updated_at)
                bucket.tokens = min(
                    effective_capacity,
                    bucket.tokens + elapsed * effective_rate,
                )
                bucket.updated_at = now
                if bucket.tokens >= 1:
                    bucket.tokens -= 1
                    return
                delay = (1 - bucket.tokens) / effective_rate
            self._sleep(delay)

    def observe(self, group: str, headers: Mapping[str, str]) -> None:
        raw_limit = headers.get("X-RateLimit-Limit")
        raw_remaining = headers.get("X-RateLimit-Remaining")
        with self._lock:
            bucket = self._bucket(group)
            if raw_limit:
                try:
                    server_limit = max(0.1, float(raw_limit))
                except ValueError:
                    server_limit = bucket.rate
                bucket.rate = server_limit
                bucket.capacity = server_limit
                bucket.tokens = min(bucket.tokens, bucket.capacity)
            if raw_remaining:
                try:
                    bucket.tokens = min(bucket.tokens, max(0.0, float(raw_remaining)))
                except ValueError:
                    pass

    def effective_rate(self, group: str) -> float:
        try:
            rate = self._buckets[group].rate
        except KeyError as exc:
            raise ValueError(f"Unknown Toss rate-limit group: {group}") from exc
        if group == "ORDER":
            now = datetime.now(ZoneInfo("Asia/Seoul"))
            if now.hour == 9 and now.minute < 10:
                return min(rate, 3.0)
        return rate

    def retry_delay(self, attempt: int, retry_after: str | None) -> float:
        server_delay = 0.0
        if retry_after:
            try:
                server_delay = max(0.0, float(retry_after))
            except ValueError:
                pass
        return max(server_delay, float(2**attempt)) + random.uniform(0, 0.25)

    def _bucket(self, group: str) -> _Bucket:
        try:
            bucket = self._buckets[group]
        except KeyError as exc:
            raise ValueError(f"Unknown Toss rate-limit group: {group}") from exc
        return bucket
