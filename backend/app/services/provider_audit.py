from dataclasses import asdict
from datetime import UTC, datetime, timedelta
import logging
from threading import Lock

from app.providers.audit import ProviderAuditMaintenanceRepository, ProviderAuditReadRepository

logger = logging.getLogger(__name__)


class ProviderAuditHistoryService:
    def __init__(self, repository: ProviderAuditReadRepository | None) -> None:
        self._repository = repository

    def recent(
        self,
        *,
        limit: int,
        offset: int,
        provider: str | None = None,
        outcome: str | None = None,
    ) -> dict[str, object]:
        if self._repository is None:
            return {
                "persistence_status": "disabled",
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
            }
        items, total = self._repository.list_recent(
            limit=limit,
            offset=offset,
            provider=provider,
            outcome=outcome,
        )
        return {
            "persistence_status": "enabled",
            "items": [asdict(item) for item in items],
            "total": total,
            "limit": limit,
            "offset": offset,
        }


class ProviderAuditMaintenanceService:
    def __init__(
        self,
        repository: ProviderAuditMaintenanceRepository | None,
        *,
        enabled: bool,
        retention_days: int,
        cleanup_hour_kst: int,
    ) -> None:
        self._repository = repository
        self._enabled = enabled
        self._retention_days = retention_days
        self._cleanup_hour_kst = cleanup_hour_kst
        self._lock = Lock()
        self._last_run_at: datetime | None = None
        self._last_cutoff: datetime | None = None
        self._last_deleted_count: int | None = None
        self._last_error_type: str | None = None

    def cleanup(self, now: datetime | None = None) -> dict[str, object]:
        if not self._enabled or self._repository is None:
            return self.status()
        run_at = now or datetime.now(UTC)
        if run_at.tzinfo is None:
            raise ValueError("Provider audit cleanup requires a timezone-aware timestamp")
        cutoff = run_at - timedelta(days=self._retention_days)
        try:
            deleted_count = self._repository.delete_before(cutoff)
        except Exception as exc:
            with self._lock:
                self._last_run_at = run_at
                self._last_cutoff = cutoff
                self._last_deleted_count = None
                self._last_error_type = type(exc).__name__
            logger.exception(
                "Provider audit cleanup failed retention_days=%s",
                self._retention_days,
            )
            return self.status()
        with self._lock:
            self._last_run_at = run_at
            self._last_cutoff = cutoff
            self._last_deleted_count = deleted_count
            self._last_error_type = None
        logger.info(
            "Provider audit cleanup completed retention_days=%s deleted_count=%s",
            self._retention_days,
            deleted_count,
        )
        return self.status()

    def status(self) -> dict[str, object]:
        with self._lock:
            if not self._enabled or self._repository is None:
                status = "disabled"
            elif self._last_error_type is not None:
                status = "failed"
            elif self._last_run_at is not None:
                status = "healthy"
            else:
                status = "pending"
            return {
                "status": status,
                "enabled": self._enabled and self._repository is not None,
                "retention_days": self._retention_days,
                "cleanup_hour_kst": self._cleanup_hour_kst,
                "last_run_at": self._last_run_at,
                "last_cutoff": self._last_cutoff,
                "last_deleted_count": self._last_deleted_count,
                "last_error_type": self._last_error_type,
            }
