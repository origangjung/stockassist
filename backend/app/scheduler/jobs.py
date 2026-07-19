import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from app.adapters.broker import BrokerAdapter
from app.config import Settings
from app.database import create_session_factory
from app.repositories.sqlalchemy import (
    SqlAlchemyCandleRepository,
    SqlAlchemyQualityLogRepository,
    SqlAlchemyStockRepository,
)
from app.alerts import SqlAlchemyAlertRepository
from app.services.alerts import ReferenceAlertService
from app.services.ingestion import CandleIngestionService
from app.database.partitions import CandlePartitionMaintenanceService
from app.repositories.provider_audit import SqlAlchemyProviderAuditRepository
from app.services.provider_audit import ProviderAuditMaintenanceService
from app.repositories.data_lifecycle import SqlAlchemyDataLifecycleRepository
from app.services.data_lifecycle import DataLifecycleMaintenanceService

logger = logging.getLogger(__name__)


def build_scheduler(
    settings: Settings,
    broker: BrokerAdapter,
    ingestion_service: CandleIngestionService | None = None,
    partition_service: CandlePartitionMaintenanceService | None = None,
    provider_audit_service: ProviderAuditMaintenanceService | None = None,
    data_lifecycle_service: DataLifecycleMaintenanceService | None = None,
) -> BackgroundScheduler:
    sessions = create_session_factory(settings.database_url)
    scheduler = BackgroundScheduler(timezone="Asia/Seoul")
    if settings.scheduler_enabled:
        service = ingestion_service or CandleIngestionService(
            broker,
            SqlAlchemyStockRepository(sessions),
            SqlAlchemyCandleRepository(sessions),
            SqlAlchemyQualityLogRepository(sessions),
        )
        for symbol in settings.scheduled_symbols:
            scheduler.add_job(
                service.ingest_daily,
                trigger="interval",
                minutes=settings.scheduler_interval_minutes,
                kwargs={"symbol": symbol, "limit": settings.scheduler_ingestion_limit},
                id=f"daily-candles:{symbol}",
                name=f"Daily candle ingestion for {symbol}",
                replace_existing=True,
                coalesce=True,
                max_instances=1,
                misfire_grace_time=60,
            )
        logger.info("Configured %s candle ingestion jobs", len(settings.scheduled_symbols))
    if settings.partition_maintenance_enabled:
        partitions = partition_service or CandlePartitionMaintenanceService(
            sessions,
            settings.partition_lookahead_months,
        )
        scheduler.add_job(
            partitions.ensure_future,
            trigger="cron",
            day=20,
            hour=3,
            minute=0,
            id="stock-candle-partitions",
            name="Ensure future monthly stock candle partitions",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=3600,
            next_run_time=datetime.now(ZoneInfo("Asia/Seoul")),
        )
        logger.info(
            "Configured monthly candle partition maintenance lookahead_months=%s",
            settings.partition_lookahead_months,
        )
    if settings.reference_alerts_enabled:
        alert_service = ReferenceAlertService(
            broker,
            SqlAlchemyAlertRepository(sessions),
        )
        scheduler.add_job(
            alert_service.evaluate_active,
            trigger="interval",
            seconds=settings.reference_alert_interval_seconds,
            id="reference-price-alerts",
            name="Reference price alert evaluation",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=30,
        )
        logger.info(
            "Configured reference alert evaluation interval_seconds=%s",
            settings.reference_alert_interval_seconds,
        )
    if settings.provider_audit_cleanup_enabled:
        audit_maintenance = provider_audit_service or ProviderAuditMaintenanceService(
            SqlAlchemyProviderAuditRepository(sessions),
            enabled=True,
            retention_days=settings.provider_audit_retention_days,
            cleanup_hour_kst=settings.provider_audit_cleanup_hour_kst,
        )
        scheduler.add_job(
            audit_maintenance.cleanup,
            trigger="cron",
            hour=settings.provider_audit_cleanup_hour_kst,
            minute=15,
            id="provider-audit-cleanup",
            name="Delete expired external provider audit logs",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=3600,
            next_run_time=datetime.now(ZoneInfo("Asia/Seoul")),
        )
        logger.info(
            "Configured provider audit cleanup retention_days=%s hour_kst=%s",
            settings.provider_audit_retention_days,
            settings.provider_audit_cleanup_hour_kst,
        )
    if settings.data_lifecycle_cleanup_enabled:
        lifecycle = data_lifecycle_service or DataLifecycleMaintenanceService(
            SqlAlchemyDataLifecycleRepository(sessions),
            enabled=True,
            retention_days=settings.data_retention_days,
            cleanup_hour_kst=settings.data_lifecycle_cleanup_hour_kst,
        )
        scheduler.add_job(
            lifecycle.cleanup,
            trigger="cron",
            hour=settings.data_lifecycle_cleanup_hour_kst,
            minute=30,
            id="operational-data-cleanup",
            name="Delete expired operational and cached content rows",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=3600,
            next_run_time=datetime.now(ZoneInfo("Asia/Seoul")),
        )
        logger.info(
            "Configured operational data cleanup retention_days=%s hour_kst=%s",
            settings.data_retention_days,
            settings.data_lifecycle_cleanup_hour_kst,
        )
    return scheduler
