from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ProviderAuditEvent:
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
    def save(self, event: ProviderAuditEvent) -> None: ...


class ProviderAuditReadRepository(Protocol):
    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        provider: str | None = None,
        outcome: str | None = None,
    ) -> tuple[list[ProviderAuditRecord], int]: ...


class ProviderAuditMaintenanceRepository(Protocol):
    def delete_before(self, cutoff: datetime) -> int: ...
