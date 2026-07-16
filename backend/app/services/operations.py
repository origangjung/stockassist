import asyncio
from datetime import UTC, datetime

from app.config import Settings
from app.observability.health import HealthService
from app.database.partitions import CandlePartitionMaintenanceService


class OperationsStatusService:
    """Build a secret-free snapshot for the authenticated operations UI."""

    def __init__(
        self,
        settings: Settings,
        health: HealthService,
        partitions: CandlePartitionMaintenanceService | None = None,
    ) -> None:
        self._settings = settings
        self._health = health
        self._partitions = partitions

    async def status(self) -> dict[str, object]:
        ready, readiness = await self._health.readiness()
        settings = self._settings
        partition_status = (
            await asyncio.to_thread(self._partitions.status)
            if settings.partition_maintenance_enabled and self._partitions is not None
            else {
                "status": "disabled",
                "items": [],
                "lookahead_months": settings.partition_lookahead_months,
            }
        )
        return {
            "status": "operational" if ready else "degraded",
            "ready": ready,
            "service": "stockpilot-api",
            "release": settings.app_release,
            "environment": settings.app_environment,
            "checked_at": datetime.now(UTC),
            "readiness": readiness,
            "providers": {
                "market": settings.stock_provider,
                "financial": settings.financial_provider,
                "disclosure": settings.disclosure_provider,
                "news": settings.news_provider,
                "investor_flow": settings.investor_flow_provider,
                "ai_report": settings.ai_report_provider,
                "prediction": settings.prediction_engine,
            },
            "features": {
                "persistence": settings.persistence_enabled,
                "realtime": settings.realtime_enabled,
                "scheduler": settings.scheduler_enabled,
                "reference_alerts": settings.reference_alerts_enabled,
                "account_sync": settings.account_sync_enabled,
                "metrics": settings.metrics_enabled,
                "sentry": settings.sentry_dsn is not None,
                "partition_maintenance": settings.partition_maintenance_enabled,
                "distributed_rate_limit": settings.rate_limit_backend == "redis",
            },
            "realtime": {
                "source": settings.realtime_source,
                "max_symbols": settings.realtime_max_symbols,
                "max_connections": settings.realtime_max_connections,
                "poll_interval_seconds": settings.realtime_poll_interval_seconds,
            },
            "partitions": partition_status,
        }
