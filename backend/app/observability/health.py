"""health 파일은 백엔드 도메인 기능을 담당한다."""

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
    """`DependencySpec` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    name: str
    required: bool
    probe: Probe | None


@dataclass(frozen=True)
class DependencyStatus:
    """`DependencyStatus` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    status: str
    required: bool
    latency_ms: float | None = None
    error_type: str | None = None


class HealthService:
    """사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다."""

    def __init__(self, dependencies: list[DependencySpec], timeout_seconds: float = 2.0):
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._dependencies = dependencies
        self._timeout_seconds = timeout_seconds

    async def readiness(self) -> tuple[bool, dict[str, object]]:
        """`readiness`은(는) 서비스와 핵심 의존성의 현재 동작 가능 상태를 반환합니다."""

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
    """`build_health_service`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

    async def database_probe() -> None:
        """`database_probe`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        if sessions is None:
            raise RuntimeError("Database session factory is unavailable")

        def ping() -> None:
            """`ping`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

            with sessions() as session:
                session.execute(text("SELECT 1"))

        await asyncio.to_thread(ping)

    async def redis_probe() -> None:
        """`redis_probe`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
