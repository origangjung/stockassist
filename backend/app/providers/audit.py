"""audit 파일은 외부 데이터 공급자 연동 기능을 담당한다."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ProviderAuditEvent:
    """`ProviderAuditEvent` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    provider: str
    method: str
    endpoint: str
    api_group: str
    outcome: str
    status_code: int | None
    error_code: str | None
    provider_request_id: str | None
    internal_request_id: str
    attempt_count: int
    duration_ms: float
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class ProviderAuditRecord:
    """저장하거나 전송할 한 건의 구조화된 데이터를 나타냅니다."""

    audit_id: int
    provider: str
    method: str
    endpoint: str
    api_group: str
    outcome: str
    status_code: int | None
    error_code: str | None
    provider_request_id: str | None
    internal_request_id: str
    attempt_count: int
    duration_ms: float
    occurred_at: datetime


class ProviderAuditSink(Protocol):
    """`ProviderAuditSink` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    def save(self, event: ProviderAuditEvent) -> None: ...


class ProviderAuditReadRepository(Protocol):
    """`ProviderAuditReadRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        provider: str | None = None,
        outcome: str | None = None,
    ) -> tuple[list[ProviderAuditRecord], int]: ...


class ProviderAuditMaintenanceRepository(Protocol):
    """`ProviderAuditMaintenanceRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    def delete_before(self, cutoff: datetime) -> int: ...
