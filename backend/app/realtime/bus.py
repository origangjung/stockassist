import asyncio
import json
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import suppress

from redis.asyncio import Redis

from app.realtime.contracts import QuoteBus, QuoteMessage


class InMemoryQuoteBus(QuoteBus):
    """Single-process bus used by isolated tests and local experiments."""

    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[QuoteMessage]]] = defaultdict(set)
        self._cache: dict[str, QuoteMessage] = {}
        self._lock = asyncio.Lock()

    async def publish(self, symbol: str, message: QuoteMessage) -> None:
        key = symbol.upper()
        async with self._lock:
            self._cache[key] = message
            queues = tuple(self._subscribers[key])
        for queue in queues:
            if queue.full():
                with suppress(asyncio.QueueEmpty):
                    queue.get_nowait()
            queue.put_nowait(message)

    async def get_cached(self, symbol: str) -> QuoteMessage | None:
        async with self._lock:
            return self._cache.get(symbol.upper())

    async def listen(self, symbol: str) -> AsyncIterator[QuoteMessage]:
        key = symbol.upper()
        queue: asyncio.Queue[QuoteMessage] = asyncio.Queue(maxsize=1)
        async with self._lock:
            self._subscribers[key].add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            async with self._lock:
                self._subscribers[key].discard(queue)
                if not self._subscribers[key]:
                    self._subscribers.pop(key, None)

    async def close(self) -> None:
        async with self._lock:
            self._subscribers.clear()
            self._cache.clear()


class RedisQuoteBus(QuoteBus):
    """Cross-process quote fan-out with a short-lived latest-value cache."""

    def __init__(self, redis_url: str, cache_ttl_seconds: int = 3) -> None:
        self._redis = Redis.from_url(redis_url, decode_responses=True)
        self._cache_ttl_seconds = cache_ttl_seconds

    @staticmethod
    def _channel(symbol: str) -> str:
        return f"stockpilot:realtime:quote:{symbol.upper()}"

    @classmethod
    def _cache_key(cls, symbol: str) -> str:
        return f"{cls._channel(symbol)}:latest"

    async def publish(self, symbol: str, message: QuoteMessage) -> None:
        payload = json.dumps(message, ensure_ascii=False, separators=(",", ":"))
        async with self._redis.pipeline(transaction=False) as pipe:
            pipe.set(self._cache_key(symbol), payload, ex=self._cache_ttl_seconds)
            pipe.publish(self._channel(symbol), payload)
            await pipe.execute()

    async def get_cached(self, symbol: str) -> QuoteMessage | None:
        payload = await self._redis.get(self._cache_key(symbol))
        if payload is None:
            return None
        message = json.loads(payload)
        return message if isinstance(message, dict) else None

    async def listen(self, symbol: str) -> AsyncIterator[QuoteMessage]:
        channel = self._channel(symbol)
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for item in pubsub.listen():
                if item.get("type") != "message":
                    continue
                message = json.loads(item["data"])
                if isinstance(message, dict):
                    yield message
        finally:
            with suppress(Exception):
                await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    async def close(self) -> None:
        await self._redis.aclose()
