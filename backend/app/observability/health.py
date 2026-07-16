import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from time import perf_counter

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.observability.metrics import record_dependency

Probe = Callable[[], Awaitable[None]]


@dataclass(frozen=True)
class DependencySpec:
    name: str
    required: bool
    probe: Probe | None


@dataclass(frozen=True)
class DependencyStatus:
    status: str
    required: bool
    latency_ms: float | None = None
    error_type: str | None = None


class HealthService:
    def __init__(self, dependencies: list[DependencySpec], timeout_seconds: float = 2.0):
        self._dependencies = dependencies
        self._timeout_seconds = timeout_seconds

    async def readiness(self) -> tuple[bool, dict[str, object]]:
        checks: dict[str, object] = {}
        ready = True
        for dependency in self._dependencies:
            if not dependency.required or dependency.probe is None:
                checks[dependency.name] = asdict(
                    DependencyStatus(status="disabled", required=False)
                )
                record_dependency(dependency.name, True)
                continue
            started_at = perf_counter()
            try:
                await asyncio.wait_for(
                    dependency.probe(),
                    timeout=self._timeout_seconds,
                )
                status = DependencyStatus(
                    status="up",
                    required=True,
                    latency_ms=round((perf_counter() - started_at) * 1000, 3),
                )
                record_dependency(dependency.name, True)
            except Exception as exc:
                status = DependencyStatus(
                    status="down",
                    required=True,
                    latency_ms=round((perf_counter() - started_at) * 1000, 3),
                    error_type=type(exc).__name__,
                )
                record_dependency(dependency.name, False)
                ready = False
            checks[dependency.name] = asdict(status)
        return ready, {
            "status": "ready" if ready else "not_ready",
            "service": "stockpilot-api",
            "checks": checks,
        }


def build_health_service(
    settings: Settings,
    sessions: sessionmaker[Session] | None,
) -> HealthService:
    async def database_probe() -> None:
        if sessions is None:
            raise RuntimeError("Database session factory is unavailable")

        def ping() -> None:
            with sessions() as session:
                session.execute(text("SELECT 1"))

        await asyncio.to_thread(ping)

    async def redis_probe() -> None:
        client = Redis.from_url(settings.redis_url, decode_responses=True)
        try:
            if not await client.ping():
                raise RuntimeError("Redis ping returned false")
        finally:
            await client.aclose()

    return HealthService(
        [
            DependencySpec("database", settings.persistence_enabled, database_probe),
            DependencySpec(
                "redis",
                settings.realtime_enabled or settings.rate_limit_backend == "redis",
                redis_probe,
            ),
        ],
        timeout_seconds=settings.health_check_timeout_seconds,
    )
