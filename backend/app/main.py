from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.adapters.broker import BrokerAdapter
from app.backtest import BacktestEngine
from app.config import get_settings
from app.database import create_session_factory
from app.database.partitions import CandlePartitionMaintenanceService
from app.core.errors import (
    http_exception_handler,
    provider_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.request_context import RequestIdMiddleware
from app.core.security import SecurityHeadersMiddleware
from app.core.rate_limit import RateLimitMiddleware, RedisSlidingWindowLimiter
from app.observability import (
    MetricsMiddleware,
    build_health_service,
    configure_logging,
    configure_sentry,
    metrics_app,
)
from app.indicators import IndicatorEngine
from app.patterns import PatternEngine
from app.api.routes import router
from app.providers import build_providers
from app.providers.errors import ProviderError
from app.financials import build_financial_provider
from app.disclosures import build_disclosure_provider
from app.news import build_news_provider
from app.investor_flow import build_investor_flow_provider
from app.prediction import build_prediction_engine
from app.ai_reports import build_ai_report_generator
from app.ai_reports.compliance import ComplianceValidator
from app.services.financial import FinancialAnalysisService
from app.services.content import DisclosureAnalysisService, NewsAnalysisService
from app.services.investor_flow import InvestorFlowService
from app.services.prediction import PredictionService
from app.services.model_registry import ModelRegistryService
from app.services.market import MarketDataService
from app.services.backtest import BacktestService
from app.services.technical import TechnicalAnalysisService
from app.services.patterns import PatternAnalysisService
from app.services.score import ScoreService
from app.services.ai_report import AIReportService
from app.services.portfolio import PortfolioService
from app.services.alerts import ReferenceAlertService
from app.services.operations import OperationsStatusService
from app.services.data_quality import DataQualityHistoryService
from app.services.provider_audit import (
    ProviderAuditHistoryService,
    ProviderAuditMaintenanceService,
)
from app.services.ingestion import CandleIngestionService, IngestionOperationsService
from app.services.data_lifecycle import DataLifecycleMaintenanceService
from app.alerts import SqlAlchemyAlertRepository
from app.realtime import build_realtime_quote_hub
from app.score import ScoreEngine, TechnicalScoreCalculator
from app.repositories.backtest import SqlAlchemyBacktestRepository
from app.repositories.provider_audit import SqlAlchemyProviderAuditRepository
from app.repositories.data_lifecycle import SqlAlchemyDataLifecycleRepository
from app.repositories.score import SqlAlchemyScoreWeightRepository
from app.repositories.sqlalchemy import (
    SqlAlchemyDisclosureRepository,
    SqlAlchemyFinancialRepository,
    SqlAlchemyInvestorFlowRepository,
    SqlAlchemyNewsRepository,
    SqlAlchemyPredictionRepository,
    SqlAlchemyAIReportRepository,
    SqlAlchemyPortfolioRepository,
    SqlAlchemyQualityLogRepository,
    SqlAlchemyStockRepository,
    SqlAlchemyCandleRepository,
)
from app.websocket import router as websocket_router

settings = get_settings()
configure_logging(settings.log_level, settings.log_format)
sentry_enabled = configure_sentry(settings)
sessions = create_session_factory(settings.database_url) if settings.persistence_enabled else None
provider_audit_repository = (
    SqlAlchemyProviderAuditRepository(sessions) if sessions is not None else None
)
provider_audit_maintenance_service = ProviderAuditMaintenanceService(
    provider_audit_repository,
    enabled=settings.provider_audit_cleanup_enabled,
    retention_days=settings.provider_audit_retention_days,
    cleanup_hour_kst=settings.provider_audit_cleanup_hour_kst,
)
data_lifecycle_repository = (
    SqlAlchemyDataLifecycleRepository(sessions) if sessions is not None else None
)
data_lifecycle_maintenance_service = DataLifecycleMaintenanceService(
    data_lifecycle_repository,
    enabled=settings.data_lifecycle_cleanup_enabled,
    retention_days=settings.data_retention_days,
    cleanup_hour_kst=settings.data_lifecycle_cleanup_hour_kst,
)
providers = build_providers(settings, audit_sink=provider_audit_repository)
broker_adapter = BrokerAdapter(providers)
market_service = MarketDataService(broker_adapter)
technical_service = TechnicalAnalysisService(broker_adapter, IndicatorEngine())
pattern_service = PatternAnalysisService(broker_adapter, PatternEngine())
backtest_repository = SqlAlchemyBacktestRepository(sessions) if sessions is not None else None
score_weight_repository = (
    SqlAlchemyScoreWeightRepository(sessions) if sessions is not None else None
)
financial_repository = SqlAlchemyFinancialRepository(sessions) if sessions is not None else None
disclosure_repository = SqlAlchemyDisclosureRepository(sessions) if sessions is not None else None
news_repository = SqlAlchemyNewsRepository(sessions) if sessions is not None else None
investor_flow_repository = (
    SqlAlchemyInvestorFlowRepository(sessions) if sessions is not None else None
)
prediction_repository = SqlAlchemyPredictionRepository(sessions) if sessions is not None else None
ai_report_repository = SqlAlchemyAIReportRepository(sessions) if sessions is not None else None
portfolio_repository = SqlAlchemyPortfolioRepository(sessions) if sessions is not None else None
alert_repository = SqlAlchemyAlertRepository(sessions) if sessions is not None else None
quality_log_repository = SqlAlchemyQualityLogRepository(sessions) if sessions is not None else None
partition_maintenance_service = (
    CandlePartitionMaintenanceService(sessions, settings.partition_lookahead_months)
    if sessions is not None
    else None
)
stock_repository = SqlAlchemyStockRepository(sessions) if sessions is not None else None
candle_repository = SqlAlchemyCandleRepository(sessions) if sessions is not None else None
financial_provider = build_financial_provider(settings)
financial_service = FinancialAnalysisService(financial_provider, financial_repository)
disclosure_provider = build_disclosure_provider(settings)
news_provider = build_news_provider(settings)
investor_flow_provider = build_investor_flow_provider(settings)
disclosure_service = DisclosureAnalysisService(disclosure_provider, disclosure_repository)
news_service = NewsAnalysisService(news_provider, news_repository)
investor_flow_service = InvestorFlowService(investor_flow_provider, investor_flow_repository)
prediction_service = PredictionService(
    broker_adapter,
    build_prediction_engine(settings.prediction_engine),
    prediction_repository,
)
model_registry_service = ModelRegistryService(prediction_repository)
backtest_service = BacktestService(broker_adapter, BacktestEngine(), backtest_repository)
score_service = ScoreService(
    broker_adapter,
    IndicatorEngine(),
    TechnicalScoreCalculator(),
    ScoreEngine(),
    score_weight_repository,
    financial=financial_service,
    news=news_service,
    disclosure=disclosure_service,
    investor_flow=investor_flow_service,
)
ai_report_generator = build_ai_report_generator(settings)
ai_report_service = AIReportService(
    market_service,
    score_service,
    prediction_service,
    investor_flow_service,
    ai_report_generator,
    ComplianceValidator(),
    ai_report_repository,
)
portfolio_service = PortfolioService(
    broker_adapter,
    sync_enabled=settings.account_sync_enabled,
    repository=portfolio_repository,
)
reference_alert_service = ReferenceAlertService(broker_adapter, alert_repository)
realtime_quote_hub = build_realtime_quote_hub(settings, broker_adapter)
health_service = build_health_service(settings, sessions)
operations_status_service = OperationsStatusService(
    settings,
    health_service,
    partition_maintenance_service,
    provider_audit_maintenance_service,
    data_lifecycle_maintenance_service,
)
data_quality_history_service = DataQualityHistoryService(quality_log_repository)
provider_audit_history_service = ProviderAuditHistoryService(provider_audit_repository)
ingestion_service = (
    CandleIngestionService(
        broker_adapter,
        stock_repository,
        candle_repository,
        quality_log_repository,
    )
    if stock_repository is not None
    and candle_repository is not None
    and quality_log_repository is not None
    else None
)
ingestion_operations_service = IngestionOperationsService(settings, ingestion_service)
distributed_rate_limiter = (
    RedisSlidingWindowLimiter(settings.redis_url)
    if settings.rate_limit_backend == "redis"
    else None
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = None
    await realtime_quote_hub.start()
    try:
        if (
            settings.scheduler_enabled
            or settings.reference_alerts_enabled
            or settings.partition_maintenance_enabled
            or settings.provider_audit_cleanup_enabled
            or settings.data_lifecycle_cleanup_enabled
        ):
            from app.scheduler import build_scheduler

            scheduler = build_scheduler(
                settings,
                broker_adapter,
                ingestion_service=ingestion_service,
                partition_service=partition_maintenance_service,
                provider_audit_service=provider_audit_maintenance_service,
                data_lifecycle_service=data_lifecycle_maintenance_service,
            )
            scheduler.start()
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)
        await realtime_quote_hub.stop()
        for provider in providers:
            provider.close()
        financial_provider.close()
        disclosure_provider.close()
        news_provider.close()
        investor_flow_provider.close()
        ai_report_generator.close()
        if distributed_rate_limiter is not None:
            await distributed_rate_limiter.aclose()


app = FastAPI(title="StockPilot AI API", version="0.1.0", lifespan=lifespan)
app.state.realtime_quote_hub = realtime_quote_hub
app.state.health_service = health_service
app.state.sentry_enabled = sentry_enabled
app.state.allowed_origins = frozenset(settings.allowed_origins)
app.state.distributed_rate_limiter = distributed_rate_limiter
app.add_middleware(
    RateLimitMiddleware,
    enabled=settings.rate_limit_enabled,
    window_seconds=settings.rate_limit_window_seconds,
    request_limit=settings.rate_limit_requests,
    expensive_request_limit=settings.expensive_rate_limit_requests,
    trust_proxy_headers=settings.trust_proxy_headers,
    backend=settings.rate_limit_backend,
    redis_url=settings.redis_url,
    distributed_limiter=distributed_rate_limiter,
)
app.add_middleware(SecurityHeadersMiddleware)
if settings.metrics_enabled:
    app.add_middleware(MetricsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ProviderError, provider_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.include_router(router)
app.include_router(websocket_router)
if settings.metrics_enabled:
    app.mount("/metrics", metrics_app())


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "stockpilot-api"}


@app.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    return {"status": "alive", "service": "stockpilot-api"}


@app.get("/health/ready", tags=["health"])
async def readiness() -> JSONResponse:
    ready, payload = await health_service.readiness()
    return JSONResponse(payload, status_code=200 if ready else 503)
