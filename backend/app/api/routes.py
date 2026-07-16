from dataclasses import asdict
from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.api.schemas import (
    ApiEnvelope,
    BacktestComparisonRequest,
    BacktestRequest,
    BacktestStrategyComparisonRequest,
    BacktestValidationRequest,
    PriceAlertCreateRequest,
    WatchlistCreateRequest,
)
from app.api.admin import require_admin_access
from app.core.compliance import compliance_metadata
from app.core.request_context import current_request_id
from app.providers.mock import UnknownSymbolError
from app.pipeline.candles import CandleInterval
from app.services.market import MarketDataService
from app.services.backtest import (
    BacktestHistoryUnavailableError,
    BacktestRunNotFoundError,
    BacktestService,
)
from app.services.technical import TechnicalAnalysisService
from app.services.patterns import PatternAnalysisService
from app.services.score import ScoreService
from app.services.financial import FinancialAnalysisService
from app.services.content import DisclosureAnalysisService, NewsAnalysisService
from app.services.investor_flow import InvestorFlowService
from app.services.prediction import PredictionService
from app.services.model_registry import (
    ModelRegistryService,
    ModelRegistryUnavailableError,
    ModelVersionNotFoundError,
)
from app.services.ai_report import AIReportService
from app.services.portfolio import PortfolioService
from app.services.alerts import (
    AlertPersistenceUnavailableError,
    ReferenceAlertService,
)
from app.services.operations import OperationsStatusService
from app.services.data_quality import DataQualityHistoryService
from app.services.provider_audit import ProviderAuditHistoryService
from app.services.ingestion import IngestionOperationsService, IngestionUnavailableError

router = APIRouter(prefix="/api/v1", tags=["market-data"])


def get_market_service() -> MarketDataService:
    from app.main import market_service

    return market_service


def get_technical_service() -> TechnicalAnalysisService:
    from app.main import technical_service

    return technical_service


def get_pattern_service() -> PatternAnalysisService:
    from app.main import pattern_service

    return pattern_service


def get_backtest_service() -> BacktestService:
    from app.main import backtest_service

    return backtest_service


def get_score_service() -> ScoreService:
    from app.main import score_service

    return score_service


def get_financial_service() -> FinancialAnalysisService:
    from app.main import financial_service

    return financial_service


def get_disclosure_service() -> DisclosureAnalysisService:
    from app.main import disclosure_service

    return disclosure_service


def get_news_service() -> NewsAnalysisService:
    from app.main import news_service

    return news_service


def get_investor_flow_service() -> InvestorFlowService:
    from app.main import investor_flow_service

    return investor_flow_service


def get_prediction_service() -> PredictionService:
    from app.main import prediction_service

    return prediction_service


def get_model_registry_service() -> ModelRegistryService:
    from app.main import model_registry_service

    return model_registry_service


def get_ai_report_service() -> AIReportService:
    from app.main import ai_report_service

    return ai_report_service


def get_portfolio_service() -> PortfolioService:
    from app.main import portfolio_service

    return portfolio_service


def get_reference_alert_service() -> ReferenceAlertService:
    from app.main import reference_alert_service

    return reference_alert_service


def get_operations_status_service() -> OperationsStatusService:
    from app.main import operations_status_service

    return operations_status_service


def get_data_quality_history_service() -> DataQualityHistoryService:
    from app.main import data_quality_history_service

    return data_quality_history_service


def get_provider_audit_history_service() -> ProviderAuditHistoryService:
    from app.main import provider_audit_history_service

    return provider_audit_history_service


def get_ingestion_operations_service() -> IngestionOperationsService:
    from app.main import ingestion_operations_service

    return ingestion_operations_service


def get_realtime_hub():
    from app.main import realtime_quote_hub

    return realtime_quote_hub


def envelope(data: dict) -> ApiEnvelope:
    return ApiEnvelope(request_id=current_request_id(), data=data, **compliance_metadata())


@router.get("/stocks/{symbol}/quote", response_model=ApiEnvelope)
def get_quote(symbol: str, service: MarketDataService = Depends(get_market_service)):
    try:
        quote, provider = service.quote(symbol)
        return envelope({**asdict(quote), "provider": provider})
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/stocks/{symbol}/candles", response_model=ApiEnvelope)
def get_candles(
    symbol: str,
    limit: int = Query(default=30, ge=1, le=365),
    service: MarketDataService = Depends(get_market_service),
):
    try:
        candles, provider = service.candles(symbol, limit)
        return envelope(
            {
                "symbol": symbol,
                "provider": provider,
                "candles": [asdict(candle) for candle in candles],
            }
        )
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/stocks/{symbol}/candles/processed", response_model=ApiEnvelope)
def get_processed_candles(
    symbol: str,
    interval: CandleInterval = Query(default=CandleInterval.DAY),
    limit: int = Query(default=90, ge=1, le=365),
    service: MarketDataService = Depends(get_market_service),
):
    try:
        result, provider = service.processed_candles(symbol, limit, interval)
        return envelope(
            {
                "symbol": symbol,
                "provider": provider,
                "interval": interval.value,
                "raw_count": result.raw_count,
                "aggregation_version": result.aggregation_version,
                "candles": [asdict(candle) for candle in result.cleaned_candles],
                "quality_logs": [asdict(log) for log in result.quality_logs],
            }
        )
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/stocks/{symbol}/orderbook", response_model=ApiEnvelope)
def get_orderbook(symbol: str, service: MarketDataService = Depends(get_market_service)):
    try:
        asks, bids, provider = service.orderbook(symbol)
        return envelope(
            {
                "symbol": symbol,
                "provider": provider,
                "asks": [asdict(level) for level in asks],
                "bids": [asdict(level) for level in bids],
            }
        )
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/stocks/{symbol}/trades", response_model=ApiEnvelope)
def get_trades(
    symbol: str,
    limit: int = Query(default=20, ge=1, le=100),
    service: MarketDataService = Depends(get_market_service),
):
    try:
        trades, provider = service.trades(symbol, limit)
        return envelope(
            {"symbol": symbol, "provider": provider, "trades": [asdict(trade) for trade in trades]}
        )
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/stocks/{symbol}", response_model=ApiEnvelope)
def get_stock_info(symbol: str, service: MarketDataService = Depends(get_market_service)):
    try:
        stock, provider = service.stock_info(symbol)
        return envelope({**asdict(stock), "provider": provider})
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/stocks/{symbol}/indicators", response_model=ApiEnvelope)
def get_indicators(
    symbol: str,
    limit: int = Query(default=180, ge=30, le=365),
    service: TechnicalAnalysisService = Depends(get_technical_service),
):
    try:
        return envelope(service.indicators(symbol, limit))
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/stocks/{symbol}/warnings", response_model=ApiEnvelope)
def get_stock_warnings(symbol: str, service: MarketDataService = Depends(get_market_service)):
    warnings, provider = service.warnings(symbol)
    return envelope(
        {
            "symbol": symbol,
            "provider": provider,
            "warnings": [asdict(warning) for warning in warnings],
        }
    )


@router.get("/stocks/{symbol}/patterns", response_model=ApiEnvelope, tags=["patterns"])
def get_patterns(
    symbol: str,
    limit: int = Query(default=180, ge=21, le=365),
    service: PatternAnalysisService = Depends(get_pattern_service),
):
    try:
        return envelope(service.patterns(symbol, limit))
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/stocks/{symbol}/financials", response_model=ApiEnvelope, tags=["financials"])
def get_financials(
    symbol: str,
    fiscal_year: int = Query(default=2025, ge=2015, le=2100),
    report_code: str = Query(default="11011", pattern=r"^1101[1-4]$"),
    service: FinancialAnalysisService = Depends(get_financial_service),
):
    return envelope(service.snapshot(symbol, fiscal_year, report_code))


@router.get("/stocks/{symbol}/disclosures", response_model=ApiEnvelope, tags=["disclosures"])
def get_disclosures(
    symbol: str,
    days: int = Query(default=90, ge=1, le=365),
    limit: int = Query(default=20, ge=1, le=100),
    service: DisclosureAnalysisService = Depends(get_disclosure_service),
):
    return envelope(service.latest(symbol, days=days, limit=limit))


@router.get("/stocks/{symbol}/news", response_model=ApiEnvelope, tags=["news"])
def get_news(
    symbol: str,
    limit: int = Query(default=20, ge=1, le=100),
    service: NewsAnalysisService = Depends(get_news_service),
):
    return envelope(service.latest(symbol, limit=limit))


@router.get("/stocks/{symbol}/investor-flow", response_model=ApiEnvelope, tags=["investor-flow"])
def get_investor_flow(
    symbol: str,
    service: InvestorFlowService = Depends(get_investor_flow_service),
):
    return envelope(service.snapshot(symbol))


@router.get("/stocks/{symbol}/prediction", response_model=ApiEnvelope, tags=["prediction"])
def get_prediction(
    symbol: str,
    horizon_days: int = Query(default=5, ge=1, le=30),
    limit: int = Query(default=180, ge=80, le=365),
    service: PredictionService = Depends(get_prediction_service),
):
    return envelope(service.predict(symbol, horizon_days=horizon_days, limit=limit))


@router.get("/stocks/{symbol}/ai-report", response_model=ApiEnvelope, tags=["ai-reports"])
def get_ai_report(
    symbol: str,
    horizon_days: int = Query(default=5, ge=1, le=30),
    limit: int = Query(default=180, ge=80, le=365),
    service: AIReportService = Depends(get_ai_report_service),
):
    return envelope(service.report(symbol, horizon_days=horizon_days, limit=limit))


@router.get(
    "/broker-accounts",
    response_model=ApiEnvelope,
    tags=["portfolios"],
    dependencies=[Depends(require_admin_access)],
)
def get_broker_accounts(service: PortfolioService = Depends(get_portfolio_service)):
    return envelope(service.accounts())


@router.get("/realtime/status", response_model=ApiEnvelope, tags=["realtime"])
def get_realtime_status(hub=Depends(get_realtime_hub)):
    return envelope(
        {
            "enabled": hub.enabled,
            "source": hub.source_name,
            "transport": hub.transport,
        }
    )


@router.post(
    "/portfolios/{account_seq}/sync",
    response_model=ApiEnvelope,
    tags=["portfolios"],
    dependencies=[Depends(require_admin_access)],
)
def sync_portfolio(
    account_seq: int,
    service: PortfolioService = Depends(get_portfolio_service),
):
    return envelope(service.sync(account_seq))


@router.post("/backtests", response_model=ApiEnvelope, tags=["backtest"])
def run_backtest(
    request: BacktestRequest, service: BacktestService = Depends(get_backtest_service)
):
    if request.fast_period >= request.slow_period:
        raise HTTPException(status_code=422, detail="fast_period must be smaller than slow_period")
    try:
        return envelope(
            service.run(
                symbol=request.symbol,
                strategy_name=request.strategy,
                limit=request.limit,
                fast_period=request.fast_period,
                slow_period=request.slow_period,
                initial_capital=request.initial_capital,
                commission_rate=request.commission_rate,
                tax_rate=request.tax_rate,
                slippage_rate=request.slippage_rate,
                engine_name=request.engine,
                max_volume_participation=request.max_volume_participation,
            )
        )
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/backtests/walk-forward",
    response_model=ApiEnvelope,
    tags=["backtest"],
)
def validate_backtest_walk_forward(
    request: BacktestValidationRequest,
    service: BacktestService = Depends(get_backtest_service),
):
    if request.fast_period >= request.slow_period:
        raise HTTPException(status_code=422, detail="fast_period must be smaller than slow_period")
    try:
        return envelope(
            service.validate_walk_forward(
                symbol=request.symbol,
                strategy_name=request.strategy,
                limit=request.limit,
                fast_period=request.fast_period,
                slow_period=request.slow_period,
                initial_capital=request.initial_capital,
                commission_rate=request.commission_rate,
                tax_rate=request.tax_rate,
                slippage_rate=request.slippage_rate,
                engine_name=request.engine,
                n_splits=request.n_splits,
                warmup_candles=request.warmup_candles,
                max_volume_participation=request.max_volume_participation,
            )
        )
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/admin/operations/status",
    response_model=ApiEnvelope,
    tags=["admin", "operations"],
    dependencies=[Depends(require_admin_access)],
)
async def get_operations_status(
    service: OperationsStatusService = Depends(get_operations_status_service),
):
    return envelope(await service.status())


@router.get(
    "/admin/data-quality",
    response_model=ApiEnvelope,
    tags=["admin", "operations", "data-quality"],
    dependencies=[Depends(require_admin_access)],
)
def get_data_quality_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    symbol: str | None = Query(default=None, pattern=r"^[0-9A-Z.-]{1,16}$"),
    severity: str | None = Query(default=None, pattern=r"^(error|warning)$"),
    service: DataQualityHistoryService = Depends(get_data_quality_history_service),
):
    return envelope(
        service.recent(
            limit=limit,
            offset=offset,
            symbol=symbol,
            severity=severity,
        )
    )


@router.get(
    "/admin/ingestion",
    response_model=ApiEnvelope,
    tags=["admin", "operations", "data-pipeline"],
    dependencies=[Depends(require_admin_access)],
)
def get_ingestion_status(
    service: IngestionOperationsService = Depends(get_ingestion_operations_service),
):
    return envelope(service.status())


@router.get(
    "/admin/provider-audits",
    response_model=ApiEnvelope,
    tags=["admin", "operations", "audit"],
    dependencies=[Depends(require_admin_access)],
)
def get_provider_audit_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    provider: str | None = Query(default=None, pattern=r"^[a-z0-9_-]{1,32}$"),
    outcome: str | None = Query(default=None, pattern=r"^(success|error|transport_error)$"),
    service: ProviderAuditHistoryService = Depends(get_provider_audit_history_service),
):
    return envelope(
        service.recent(
            limit=limit,
            offset=offset,
            provider=provider,
            outcome=outcome,
        )
    )


@router.post(
    "/admin/ingestion/{symbol}",
    response_model=ApiEnvelope,
    tags=["admin", "operations", "data-pipeline"],
    dependencies=[Depends(require_admin_access)],
)
def trigger_candle_ingestion(
    symbol: str = Path(pattern=r"^[0-9A-Z.-]{1,16}$"),
    limit: int | None = Query(default=None, ge=30, le=365),
    service: IngestionOperationsService = Depends(get_ingestion_operations_service),
):
    try:
        return envelope(service.ingest(symbol, limit=limit))
    except IngestionUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/admin/backtests",
    response_model=ApiEnvelope,
    tags=["admin"],
    dependencies=[Depends(require_admin_access)],
)
def get_backtest_history(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    symbol: str | None = Query(default=None, pattern=r"^[0-9A-Z]{1,16}$"),
    service: BacktestService = Depends(get_backtest_service),
):
    return envelope(service.history(limit=limit, offset=offset, symbol=symbol))


@router.post(
    "/admin/backtests/compare",
    response_model=ApiEnvelope,
    tags=["admin", "backtest"],
    dependencies=[Depends(require_admin_access)],
)
def compare_backtest_engines(
    request: BacktestComparisonRequest,
    service: BacktestService = Depends(get_backtest_service),
):
    if request.fast_period >= request.slow_period:
        raise HTTPException(status_code=422, detail="fast_period must be smaller than slow_period")
    try:
        return envelope(
            service.compare_engines(
                symbol=request.symbol,
                strategy_name=request.strategy,
                limit=request.limit,
                fast_period=request.fast_period,
                slow_period=request.slow_period,
                initial_capital=request.initial_capital,
                commission_rate=request.commission_rate,
                tax_rate=request.tax_rate,
                slippage_rate=request.slippage_rate,
                max_volume_participation=request.max_volume_participation,
            )
        )
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/admin/backtests/strategies/compare",
    response_model=ApiEnvelope,
    tags=["admin", "backtest"],
    dependencies=[Depends(require_admin_access)],
)
def compare_backtest_strategies(
    request: BacktestStrategyComparisonRequest,
    service: BacktestService = Depends(get_backtest_service),
):
    if request.fast_period >= request.slow_period:
        raise HTTPException(status_code=422, detail="fast_period must be smaller than slow_period")
    try:
        return envelope(
            service.compare_strategies(
                symbol=request.symbol,
                engine_name=request.engine,
                limit=request.limit,
                fast_period=request.fast_period,
                slow_period=request.slow_period,
                initial_capital=request.initial_capital,
                commission_rate=request.commission_rate,
                tax_rate=request.tax_rate,
                slippage_rate=request.slippage_rate,
                max_volume_participation=request.max_volume_participation,
            )
        )
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/admin/backtests/{run_id}",
    response_model=ApiEnvelope,
    tags=["admin"],
    dependencies=[Depends(require_admin_access)],
)
def get_backtest_history_detail(
    run_id: str,
    service: BacktestService = Depends(get_backtest_service),
):
    try:
        return envelope(service.history_detail(run_id))
    except BacktestHistoryUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except BacktestRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/admin/models",
    response_model=ApiEnvelope,
    tags=["admin", "prediction"],
    dependencies=[Depends(require_admin_access)],
)
def get_model_versions(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    symbol: str | None = Query(default=None, pattern=r"^[0-9A-Z.-]{1,16}$"),
    algorithm: str | None = Query(default=None, pattern=r"^[a-z0-9_-]{1,32}$"),
    horizon_days: int | None = Query(default=None, ge=1, le=30),
    service: ModelRegistryService = Depends(get_model_registry_service),
):
    return envelope(
        service.versions(
            limit=limit,
            offset=offset,
            symbol=symbol,
            algorithm=algorithm,
            horizon_days=horizon_days,
        )
    )


@router.post(
    "/admin/models/{version}/promote",
    response_model=ApiEnvelope,
    tags=["admin", "prediction"],
    dependencies=[Depends(require_admin_access)],
)
def promote_model_version(
    version: str = Path(pattern=r"^[a-z0-9-]{1,64}$"),
    service: ModelRegistryService = Depends(get_model_registry_service),
):
    try:
        return envelope(service.promote(version))
    except ModelRegistryUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ModelVersionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/admin/watchlist",
    response_model=ApiEnvelope,
    tags=["admin"],
    dependencies=[Depends(require_admin_access)],
)
def get_watchlist(
    service: ReferenceAlertService = Depends(get_reference_alert_service),
):
    return envelope(service.watchlist())


@router.post(
    "/admin/watchlist",
    response_model=ApiEnvelope,
    tags=["admin"],
    dependencies=[Depends(require_admin_access)],
)
def add_watchlist_item(
    request: WatchlistCreateRequest,
    service: ReferenceAlertService = Depends(get_reference_alert_service),
):
    try:
        return envelope(service.add_watchlist(request.symbol))
    except AlertPersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete(
    "/admin/watchlist/{symbol}",
    response_model=ApiEnvelope,
    tags=["admin"],
    dependencies=[Depends(require_admin_access)],
)
def remove_watchlist_item(
    symbol: str,
    service: ReferenceAlertService = Depends(get_reference_alert_service),
):
    try:
        return envelope(service.remove_watchlist(symbol))
    except AlertPersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "/admin/alerts",
    response_model=ApiEnvelope,
    tags=["admin"],
    dependencies=[Depends(require_admin_access)],
)
def get_reference_alerts(
    status: str | None = Query(default=None, pattern=r"^(active|triggered|disabled)$"),
    service: ReferenceAlertService = Depends(get_reference_alert_service),
):
    return envelope(service.alerts(status=status))


@router.post(
    "/admin/alerts",
    response_model=ApiEnvelope,
    tags=["admin"],
    dependencies=[Depends(require_admin_access)],
)
def create_reference_alert(
    request: PriceAlertCreateRequest,
    service: ReferenceAlertService = Depends(get_reference_alert_service),
):
    try:
        return envelope(
            service.create_alert(
                request.symbol,
                request.condition,
                request.target_price,
            )
        )
    except AlertPersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/admin/alerts/evaluate",
    response_model=ApiEnvelope,
    tags=["admin"],
    dependencies=[Depends(require_admin_access)],
)
def evaluate_reference_alerts(
    service: ReferenceAlertService = Depends(get_reference_alert_service),
):
    try:
        return envelope(service.evaluate_active())
    except AlertPersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.delete(
    "/admin/alerts/{alert_id}",
    response_model=ApiEnvelope,
    tags=["admin"],
    dependencies=[Depends(require_admin_access)],
)
def disable_reference_alert(
    alert_id: str,
    service: ReferenceAlertService = Depends(get_reference_alert_service),
):
    try:
        return envelope(service.disable_alert(alert_id))
    except AlertPersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/stocks/{symbol}/score", response_model=ApiEnvelope, tags=["score"])
def get_score(
    symbol: str,
    limit: int = Query(default=180, ge=30, le=365),
    service: ScoreService = Depends(get_score_service),
):
    try:
        return envelope(service.score(symbol, limit))
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
