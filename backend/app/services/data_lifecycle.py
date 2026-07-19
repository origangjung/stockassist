from datetime import UTC, datetime, timedelta
import logging
from threading import Lock

from app.data_lifecycle import DataLifecycleRepository

logger = logging.getLogger(__name__)


class DataLifecycleMaintenanceService:
    def __init__(
        self,
        repository: DataLifecycleRepository | None,
        *,
        enabled: bool,
        retention_days: dict[str, int],
        cleanup_hour_kst: int,
    ) -> None:
        self._repository = repository
        self._enabled = enabled
        self._retention_days = dict(retention_days)
        self._cleanup_hour_kst = cleanup_hour_kst
        self._lock = Lock()
        self._last_run_at: datetime | None = None
        self._last_deleted_counts: dict[str, int] | None = None
        self._last_error_type: str | None = None

    def preview(self, now: datetime | None = None) -> dict[str, object]:
        if self._repository is None:
            return {**self.status(), "eligible_counts": None, "cutoffs": None}
        run_at = self._aware_now(now)
        cutoffs = self._cutoffs(run_at)
        try:
            eligible = self._repository.count_before(cutoffs)
        except Exception as exc:
            logger.exception("Data lifecycle preview failed")
            return {
                **self.status(),
                "preview_status": "failed",
                "eligible_counts": None,
                "cutoffs": cutoffs,
                "preview_error_type": type(exc).__name__,
            }
        return {
            **self.status(),
            "preview_status": "ready",
            "eligible_counts": eligible,
            "cutoffs": cutoffs,
            "preview_error_type": None,
        }

    def cleanup(self, now: datetime | None = None) -> dict[str, object]:
        if not self._enabled or self._repository is None:
            return self.status()
        run_at = self._aware_now(now)
        cutoffs = self._cutoffs(run_at)
        try:
            deleted = self._repository.delete_before(cutoffs)
        except Exception as exc:
            with self._lock:
                self._last_run_at = run_at
                self._last_deleted_counts = None
                self._last_error_type = type(exc).__name__
            logger.exception("Data lifecycle cleanup failed")
            return self.status()
        with self._lock:
            self._last_run_at = run_at
            self._last_deleted_counts = deleted
            self._last_error_type = None
        logger.info("Data lifecycle cleanup completed deleted_counts=%s", deleted)
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
                "retention_days": dict(self._retention_days),
                "cleanup_hour_kst": self._cleanup_hour_kst,
                "last_run_at": self._last_run_at,
                "last_deleted_counts": (
                    dict(self._last_deleted_counts)
                    if self._last_deleted_counts is not None
                    else None
                ),
                "last_error_type": self._last_error_type,
            }

    def _cutoffs(self, now: datetime) -> dict[str, datetime]:
        return {
            dataset: now - timedelta(days=retention_days)
            for dataset, retention_days in self._retention_days.items()
        }

    @staticmethod
    def _aware_now(now: datetime | None) -> datetime:
        value = now or datetime.now(UTC)
        if value.tzinfo is None:
            raise ValueError("Data lifecycle maintenance requires a timezone-aware timestamp")
        return value
