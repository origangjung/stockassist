"""benchmark_redis_runtime 파일은 개발·운영·보안 점검 기능을 담당한다."""

import argparse
import asyncio
import os
from time import perf_counter

from app.core.rate_limit import RedisSlidingWindowLimiter
from app.realtime.bus import RedisQuoteBus


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description="Validate Redis runtime behavior without secrets")
    parser.add_argument("--limiter-requests", type=int, default=500)
    parser.add_argument("--limiter-limit", type=int, default=240)
    parser.add_argument("--subscribers", type=int, default=10)
    parser.add_argument("--messages", type=int, default=100)
    return parser.parse_args()


async def receive_messages(bus: RedisQuoteBus, symbol: str, count: int) -> list[int]:
    """`receive_messages`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    received: list[int] = []
    stream = bus.listen(symbol)
    try:
        while len(received) < count:
            message = await asyncio.wait_for(anext(stream), timeout=10)
            received.append(int(message["sequence"]))
    finally:
        await stream.aclose()
    return received


async def benchmark(args: argparse.Namespace) -> None:
    """`benchmark`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        raise RuntimeError("REDIS_URL is required")
    if min(
        args.limiter_requests,
        args.limiter_limit,
        args.subscribers,
        args.messages,
    ) < 1:
        raise ValueError("benchmark counts must be positive")

    limiter = RedisSlidingWindowLimiter(redis_url)
    limiter_key = f"benchmark:{os.getpid()}"
    await limiter.clear(limiter_key)
    limiter_start = perf_counter()
    results = await asyncio.gather(
        *(
            limiter.consume(limiter_key, limit=args.limiter_limit, window=60)
            for _ in range(args.limiter_requests)
        )
    )
    limiter_elapsed = perf_counter() - limiter_start
    allowed = sum(result[0] for result in results)
    rejected = len(results) - allowed
    expected_allowed = min(args.limiter_requests, args.limiter_limit)
    if allowed != expected_allowed:
        raise RuntimeError(f"limiter mismatch: expected {expected_allowed}, received {allowed}")
    await limiter.clear(limiter_key)
    await limiter.aclose()

    symbol = f"BENCH{os.getpid()}"
    buses = [RedisQuoteBus(redis_url, cache_ttl_seconds=2) for _ in range(args.subscribers)]
    publisher = RedisQuoteBus(redis_url, cache_ttl_seconds=2)
    listeners = [
        asyncio.create_task(receive_messages(bus, symbol, args.messages)) for bus in buses
    ]
    await asyncio.sleep(0.25)
    pubsub_start = perf_counter()
    for sequence in range(args.messages):
        await publisher.publish(
            symbol,
            {"type": "quote", "symbol": symbol, "sequence": sequence},
        )
    received = await asyncio.gather(*listeners)
    pubsub_elapsed = perf_counter() - pubsub_start
    expected_sequence = list(range(args.messages))
    if any(messages != expected_sequence for messages in received):
        raise RuntimeError("Pub/Sub message loss or ordering mismatch")

    cached = await publisher.get_cached(symbol)
    if cached is None or cached.get("sequence") != args.messages - 1:
        raise RuntimeError("latest-value cache mismatch")
    await asyncio.sleep(2.2)
    if await publisher.get_cached(symbol) is not None:
        raise RuntimeError("latest-value cache did not expire")

    for bus in buses:
        await bus.close()
    await publisher.close()

    deliveries = args.subscribers * args.messages
    print(
        "redis_benchmark=ok "
        f"limiter_requests={args.limiter_requests} allowed={allowed} rejected={rejected} "
        f"limiter_rps={args.limiter_requests / limiter_elapsed:.1f} "
        f"subscribers={args.subscribers} messages={args.messages} deliveries={deliveries} "
        f"pubsub_deliveries_per_second={deliveries / pubsub_elapsed:.1f} cache_ttl=ok"
    )


if __name__ == "__main__":
    asyncio.run(benchmark(parse_args()))
