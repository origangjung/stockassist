"""시세·분석·운영·관리 기능의 HTTP 계약을 정의한다.

라우트 함수는 HTTP 입력을 검증하고 애플리케이션 서비스를 호출한 뒤 공통 응답 형식으로
감싼다. 공급자 선택과 도메인 계산은 HTTP 없이도 테스트할 수 있도록 하위 계층에 둔다.
"""

from dataclasses import asdict
from datetime import date, datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.api.schemas import (
    ApiEnvelope,
    BacktestComparisonRequest,
    BacktestRequest,
    BacktestStrategyComparisonRequest,
    BacktestValidationRequest,
    CorporateActionApprovalRequest,
    FundAllocationProposalRequest,
    PriceAlertCreateRequest,
    PaperOrderRequest,
    TossConditionalOrderRequest,
    TossMutationConfirmation,
    TossOrderCreateRequest,
    TossOrderModifyRequest,
    WatchlistCreateRequest,
)
from app.api.admin import require_admin_access
from app.core.compliance import compliance_metadata
from app.core.request_context import current_request_id
from app.providers.mock import UnknownSymbolError
from app.pipeline.candles import CandleInterval
from app.corporate_actions import (
    CorporateActionIngestionUnavailableError,
    CorporateActionAdjustmentUnavailableError,
    CorporateActionRevisionConflictError,
    CorporateActionSourceNotFoundError,
    UntrustedCorporateActionSourceError,
)
from app.corporate_actions.approval_contracts import (
    CorporateActionApprovalConflictError,
    CorporateActionApprovalUnavailableError,
)
from app.services.market import MarketDataService
from app.services.toss_open_api import TossOpenApiService
from app.services.backtest import (
    BacktestHistoryUnavailableError,
    BacktestRunNotFoundError,
    BacktestService,
)
from app.services.technical import TechnicalAnalysisService
from app.services.patterns import PatternAnalysisService
from app.services.score import ScoreService
from app.services.financial import FinancialAnalysisService
from app.financials.valuation import ValuationAnalysisService
from app.services.content import DisclosureAnalysisService, NewsAnalysisService
from app.services.investor_flow import InvestorFlowService
from app.services.prediction import PredictionService
from app.services.model_registry import (
    ModelArtifactValidationError,
    ModelRegistryService,
    ModelRegistryUnavailableError,
    ModelVersionNotFoundError,
)
from app.services.local_ai_readiness import LocalAiReadinessService
from app.services.ai_report import AIReportService
from app.services.portfolio import PortfolioService
from app.services.paper_trading import PaperTradingService
from app.fund_management.contracts import FundManagementError
from app.fund_management.service import FundManagementService
from app.paper_trading.contracts import (
    InsufficientPaperCashError,
    InsufficientPaperPositionError,
    PaperRiskLimitError,
)
from app.services.alerts import (
    AlertPersistenceUnavailableError,
    ReferenceAlertService,
)
from app.services.operations import OperationsStatusService
from app.services.data_quality import DataQualityHistoryService
from app.services.candle_inventory import CandlePriceBasisInventoryService
from app.services.provider_audit import (
    ProviderAuditHistoryService,
    ProviderAuditMaintenanceService,
)
from app.services.ingestion import IngestionOperationsService, IngestionUnavailableError
from app.services.data_lifecycle import DataLifecycleMaintenanceService
from app.services.corporate_actions import (
    CorporateActionApprovalService,
    CorporateActionCandidateService,
    CorporateActionIngestionService,
    CorporateActionService,
)

router = APIRouter(prefix="/api/v1", tags=["market-data"])


def get_market_service() -> MarketDataService:
    """`get_market_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import market_service

    return market_service


def get_toss_open_api_service() -> TossOpenApiService:
    """현재 프로세스의 토스 확장 시장 데이터 서비스를 반환한다."""
    from app.main import toss_open_api_service

    return toss_open_api_service


def get_technical_service() -> TechnicalAnalysisService:
    """`get_technical_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import technical_service

    return technical_service


def get_pattern_service() -> PatternAnalysisService:
    """`get_pattern_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import pattern_service

    return pattern_service


def get_backtest_service() -> BacktestService:
    """`get_backtest_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import backtest_service

    return backtest_service


def get_score_service() -> ScoreService:
    """`get_score_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import score_service

    return score_service


def get_financial_service() -> FinancialAnalysisService:
    """`get_financial_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import financial_service

    return financial_service


def get_valuation_service() -> ValuationAnalysisService:
    """`get_valuation_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import valuation_service

    return valuation_service


def get_disclosure_service() -> DisclosureAnalysisService:
    """`get_disclosure_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import disclosure_service

    return disclosure_service


def get_news_service() -> NewsAnalysisService:
    """`get_news_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import news_service

    return news_service


def get_investor_flow_service() -> InvestorFlowService:
    """`get_investor_flow_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import investor_flow_service

    return investor_flow_service


def get_prediction_service() -> PredictionService:
    """`get_prediction_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import prediction_service

    return prediction_service


def get_model_registry_service() -> ModelRegistryService:
    """`get_model_registry_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import model_registry_service

    return model_registry_service


def get_local_ai_readiness_service() -> LocalAiReadinessService:
    """관리자용 직접 학습 AI 준비도 서비스를 반환한다."""

    from app.main import local_ai_readiness_service

    return local_ai_readiness_service


def get_ai_report_service() -> AIReportService:
    """`get_ai_report_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import ai_report_service

    return ai_report_service


def get_portfolio_service() -> PortfolioService:
    """`get_portfolio_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import portfolio_service

    return portfolio_service


def get_paper_trading_service() -> PaperTradingService:
    """프로세스에서 공유하는 실제 주문과 격리된 모의투자 서비스를 반환한다."""
    from app.main import paper_trading_service

    return paper_trading_service


def get_fund_management_service() -> FundManagementService:
    """프로세스에서 공유하는 모의 자금운용 제안 서비스를 반환한다."""
    from app.main import fund_management_service

    return fund_management_service


def get_reference_alert_service() -> ReferenceAlertService:
    """`get_reference_alert_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import reference_alert_service

    return reference_alert_service


def get_operations_status_service() -> OperationsStatusService:
    """`get_operations_status_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import operations_status_service

    return operations_status_service


def get_data_quality_history_service() -> DataQualityHistoryService:
    """`get_data_quality_history_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import data_quality_history_service

    return data_quality_history_service


def get_candle_price_basis_inventory_service() -> CandlePriceBasisInventoryService:
    """`get_candle_price_basis_inventory_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import candle_price_basis_inventory_service

    return candle_price_basis_inventory_service


def get_provider_audit_history_service() -> ProviderAuditHistoryService:
    """`get_provider_audit_history_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import provider_audit_history_service

    return provider_audit_history_service


def get_provider_audit_maintenance_service() -> ProviderAuditMaintenanceService:
    """`get_provider_audit_maintenance_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import provider_audit_maintenance_service

    return provider_audit_maintenance_service


def get_data_lifecycle_maintenance_service() -> DataLifecycleMaintenanceService:
    """`get_data_lifecycle_maintenance_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import data_lifecycle_maintenance_service

    return data_lifecycle_maintenance_service


def get_corporate_action_service() -> CorporateActionService:
    """`get_corporate_action_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import corporate_action_service

    return corporate_action_service


def get_corporate_action_ingestion_service() -> CorporateActionIngestionService:
    """`get_corporate_action_ingestion_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import corporate_action_ingestion_service

    return corporate_action_ingestion_service


def get_corporate_action_candidate_service() -> CorporateActionCandidateService:
    """`get_corporate_action_candidate_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import corporate_action_candidate_service

    return corporate_action_candidate_service


def get_corporate_action_approval_service() -> CorporateActionApprovalService:
    """`get_corporate_action_approval_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import corporate_action_approval_service

    return corporate_action_approval_service


def get_ingestion_operations_service() -> IngestionOperationsService:
    """`get_ingestion_operations_service`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import ingestion_operations_service

    return ingestion_operations_service


def get_realtime_hub():
    """`get_realtime_hub`은(는) 필요한 데이터를 조회해 반환합니다."""

    from app.main import realtime_quote_hub

    return realtime_quote_hub


def envelope(data: dict) -> ApiEnvelope:
    """`envelope`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return ApiEnvelope(request_id=current_request_id(), data=data, **compliance_metadata())


@router.get("/stocks/search", response_model=ApiEnvelope, tags=["stock-search"])
def search_stocks(
    q: str = Query(min_length=1, max_length=80),
    limit: int = Query(default=12, ge=1, le=30),
    service: TossOpenApiService = Depends(get_toss_open_api_service),
):
    """토스 전체 종목 원장에서 티커와 한글·영문 종목명을 검색한다."""
    return envelope(service.search_stocks(q, limit))


@router.get("/market/overview", response_model=ApiEnvelope, tags=["market-overview"])
def get_market_overview(
    service: TossOpenApiService = Depends(get_toss_open_api_service),
):
    """시장 지표·환율·장 운영·거래대금 상위 종목을 한 번에 조회한다."""
    return envelope(service.market_overview())


@router.get("/market/rankings", response_model=ApiEnvelope, tags=["market-overview"])
def get_market_rankings(
    ranking_type: Literal[
        "MARKET_TRADING_AMOUNT",
        "MARKET_TRADING_VOLUME",
        "TOP_GAINERS",
        "TOP_LOSERS",
        "TOSS_SECURITIES_TRADING_AMOUNT",
        "TOSS_SECURITIES_TRADING_VOLUME",
    ] = Query(alias="type"),
    market_country: Literal["KR", "US"] = Query(default="KR"),
    duration: Literal["realtime", "1d", "1w", "1mo", "3mo", "6mo", "1y"] = Query(
        default="1d"
    ),
    count: int = Query(default=20, ge=1, le=100),
    service: TossOpenApiService = Depends(get_toss_open_api_service),
):
    """시장·토스 체결 기준의 거래대금·거래량·등락률 랭킹을 조회한다."""
    if ranking_type in {"TOP_GAINERS", "TOP_LOSERS"} and duration == "realtime":
        raise HTTPException(status_code=422, detail="등락률 랭킹은 realtime을 지원하지 않습니다")
    return envelope(service.rankings(ranking_type, market_country, duration, count))


@router.get(
    "/market/indicators/{symbol}",
    response_model=ApiEnvelope,
    tags=["market-overview"],
)
def get_market_indicator_history(
    symbol: Literal[
        "KOSPI",
        "KOSDAQ",
        "KR_BOND_2Y",
        "KR_BOND_3Y",
        "KR_BOND_5Y",
        "KR_BOND_10Y",
        "KR_BOND_20Y",
        "KR_BOND_30Y",
    ],
    interval: Literal["1m", "1d"] = Query(default="1d"),
    count: int = Query(default=30, ge=1, le=200),
    service: TossOpenApiService = Depends(get_toss_open_api_service),
):
    """국내 지수·국채 시계열과 지수 투자자별 매매대금을 조회한다."""
    if symbol.startswith("KR_BOND_") and interval == "1m":
        raise HTTPException(status_code=422, detail="국채 지표는 일봉만 지원합니다")
    return envelope(
        service.market_indicator_history(symbol, interval=interval, count=count)
    )


@router.get("/paper-portfolios/{account_id}", response_model=ApiEnvelope, tags=["paper-trading"])
def get_paper_portfolio(
    account_id: str = Path(pattern=r"^[0-9a-f-]{36}$"),
    service: PaperTradingService = Depends(get_paper_trading_service),
):
    """브라우저 UUID에 대응하는 모의 계좌 평가 결과를 조회한다."""
    return envelope(service.snapshot(account_id))


@router.post("/paper-portfolios/{account_id}/orders", response_model=ApiEnvelope, tags=["paper-trading"])
def create_paper_order(
    request: PaperOrderRequest,
    account_id: str = Path(pattern=r"^[0-9a-f-]{36}$"),
    service: PaperTradingService = Depends(get_paper_trading_service),
):
    """현재가 기반 모의 시장가 주문을 원장에 한 번만 체결한다."""
    try:
        return envelope(service.execute(account_id, **request.model_dump()))
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (
        InsufficientPaperCashError,
        InsufficientPaperPositionError,
        PaperRiskLimitError,
    ) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/paper-portfolios/{account_id}/reset", response_model=ApiEnvelope, tags=["paper-trading"])
def reset_paper_portfolio(
    account_id: str = Path(pattern=r"^[0-9a-f-]{36}$"),
    service: PaperTradingService = Depends(get_paper_trading_service),
):
    """실제 계좌에는 영향 없이 해당 모의 계좌만 초기화한다."""
    return envelope(service.reset(account_id))


@router.post(
    "/paper-portfolios/{account_id}/allocation-proposals",
    response_model=ApiEnvelope,
    tags=["fund-management"],
)
def create_allocation_proposal(
    request: FundAllocationProposalRequest,
    account_id: str = Path(pattern=r"^[0-9a-f-]{36}$"),
    service: FundManagementService = Depends(get_fund_management_service),
):
    """과거 가격과 모의 보유량으로 실행되지 않는 자금배분 제안을 생성한다."""
    try:
        return envelope(service.propose(account_id, **request.model_dump()))
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FundManagementError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/stocks/{symbol}/quote", response_model=ApiEnvelope)
def get_quote(symbol: str, service: MarketDataService = Depends(get_market_service)):
    """`get_quote`은(는) 필요한 데이터를 조회해 반환합니다."""

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
    """`get_candles`은(는) 필요한 데이터를 조회해 반환합니다."""

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
    """`get_processed_candles`은(는) 필요한 데이터를 조회해 반환합니다."""

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
    """`get_orderbook`은(는) 필요한 데이터를 조회해 반환합니다."""

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
    """`get_trades`은(는) 필요한 데이터를 조회해 반환합니다."""

    try:
        trades, provider = service.trades(symbol, limit)
        return envelope(
            {"symbol": symbol, "provider": provider, "trades": [asdict(trade) for trade in trades]}
        )
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/stocks/{symbol}", response_model=ApiEnvelope)
def get_stock_info(symbol: str, service: MarketDataService = Depends(get_market_service)):
    """`get_stock_info`은(는) 필요한 데이터를 조회해 반환합니다."""

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
    """`get_indicators`은(는) 필요한 데이터를 조회해 반환합니다."""

    try:
        return envelope(service.indicators(symbol, limit))
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/stocks/{symbol}/warnings", response_model=ApiEnvelope)
def get_stock_warnings(symbol: str, service: MarketDataService = Depends(get_market_service)):
    """`get_stock_warnings`은(는) 필요한 데이터를 조회해 반환합니다."""

    warnings, provider = service.warnings(symbol)
    return envelope(
        {
            "symbol": symbol,
            "provider": provider,
            "warnings": [asdict(warning) for warning in warnings],
        }
    )


@router.get(
    "/stocks/{symbol}/microstructure",
    response_model=ApiEnvelope,
    tags=["market-data"],
)
def get_stock_microstructure(
    symbol: str = Path(pattern=r"^[0-9A-Z.-]{1,16}$"),
    trade_limit: int = Query(default=20, ge=1, le=50),
    service: TossOpenApiService = Depends(get_toss_open_api_service),
):
    """호가·체결·가격 제한·투자 유의 정보를 한 화면용 응답으로 조립한다."""
    return envelope(service.stock_microstructure(symbol, trade_limit))


@router.get(
    "/stocks/{symbol}/toss-trends",
    response_model=ApiEnvelope,
    tags=["investor-flow"],
)
def get_toss_stock_trends(
    symbol: str = Path(pattern=r"^[0-9]{6}$"),
    count: int = Query(default=20, ge=1, le=100),
    service: TossOpenApiService = Depends(get_toss_open_api_service),
):
    """국내 종목의 투자자·프로그램·공매도·신용·대차 흐름을 조회한다."""
    return envelope(service.stock_trends(symbol, count))


@router.get("/stocks/{symbol}/patterns", response_model=ApiEnvelope, tags=["patterns"])
def get_patterns(
    symbol: str,
    limit: int = Query(default=180, ge=21, le=365),
    service: PatternAnalysisService = Depends(get_pattern_service),
):
    """`get_patterns`은(는) 필요한 데이터를 조회해 반환합니다."""

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
    """`get_financials`은(는) 필요한 데이터를 조회해 반환합니다."""

    return envelope(service.snapshot(symbol, fiscal_year, report_code))


@router.get("/stocks/{symbol}/valuation", response_model=ApiEnvelope, tags=["financials"])
def get_valuation(
    symbol: str,
    fiscal_year: int = Query(default=2025, ge=2015, le=2100),
    report_code: str = Query(default="11011", pattern=r"^1101[1-4]$"),
    service: ValuationAnalysisService = Depends(get_valuation_service),
):
    """`get_valuation`은(는) 필요한 데이터를 조회해 반환합니다."""

    return envelope(service.analyze(symbol, fiscal_year, report_code))


@router.get("/stocks/{symbol}/disclosures", response_model=ApiEnvelope, tags=["disclosures"])
def get_disclosures(
    symbol: str,
    days: int = Query(default=90, ge=1, le=365),
    limit: int = Query(default=20, ge=1, le=100),
    service: DisclosureAnalysisService = Depends(get_disclosure_service),
):
    """`get_disclosures`은(는) 필요한 데이터를 조회해 반환합니다."""

    return envelope(service.latest(symbol, days=days, limit=limit))


@router.get("/stocks/{symbol}/news", response_model=ApiEnvelope, tags=["news"])
def get_news(
    symbol: str,
    limit: int = Query(default=20, ge=1, le=100),
    service: NewsAnalysisService = Depends(get_news_service),
):
    """`get_news`은(는) 필요한 데이터를 조회해 반환합니다."""

    return envelope(service.latest(symbol, limit=limit))


@router.get("/stocks/{symbol}/investor-flow", response_model=ApiEnvelope, tags=["investor-flow"])
def get_investor_flow(
    symbol: str,
    service: InvestorFlowService = Depends(get_investor_flow_service),
):
    """`get_investor_flow`은(는) 필요한 데이터를 조회해 반환합니다."""

    return envelope(service.snapshot(symbol))


@router.get("/stocks/{symbol}/prediction", response_model=ApiEnvelope, tags=["prediction"])
def get_prediction(
    symbol: str,
    horizon_days: int = Query(default=5, ge=1, le=30),
    limit: int = Query(default=180, ge=80, le=365),
    service: PredictionService = Depends(get_prediction_service),
):
    """`get_prediction`은(는) 필요한 데이터를 조회해 반환합니다."""

    return envelope(service.predict(symbol, horizon_days=horizon_days, limit=limit))


@router.get("/stocks/{symbol}/ai-report", response_model=ApiEnvelope, tags=["ai-reports"])
def get_ai_report(
    symbol: str,
    horizon_days: int = Query(default=5, ge=1, le=30),
    limit: int = Query(default=180, ge=80, le=365),
    service: AIReportService = Depends(get_ai_report_service),
):
    """`get_ai_report`은(는) 필요한 데이터를 조회해 반환합니다."""

    return envelope(service.report(symbol, horizon_days=horizon_days, limit=limit))


@router.get(
    "/broker-accounts",
    response_model=ApiEnvelope,
    tags=["portfolios"],
    dependencies=[Depends(require_admin_access)],
)
def get_broker_accounts(service: PortfolioService = Depends(get_portfolio_service)):
    """`get_broker_accounts`은(는) 필요한 데이터를 조회해 반환합니다."""

    return envelope(service.accounts())


@router.get("/realtime/status", response_model=ApiEnvelope, tags=["realtime"])
def get_realtime_status(hub=Depends(get_realtime_hub)):
    """`get_realtime_status`은(는) 필요한 데이터를 조회해 반환합니다."""

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
    """`sync_portfolio`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return envelope(service.sync(account_seq))


@router.get(
    "/admin/toss/accounts/{account_seq}/workspace",
    response_model=ApiEnvelope,
    tags=["admin", "toss"],
    dependencies=[Depends(require_admin_access)],
)
def get_toss_account_workspace(
    account_seq: int = Path(gt=0),
    symbol: str | None = Query(default=None, pattern=r"^[0-9A-Z.-]{1,16}$"),
    currency: str = Query(default="KRW", pattern=r"^(KRW|USD)$"),
    service: TossOpenApiService = Depends(get_toss_open_api_service),
):
    """보유 자산·주문 내역·주문 가능 정보가 포함된 읽기 전용 작업 공간을 반환한다."""
    return envelope(service.account_workspace(account_seq, symbol=symbol, currency=currency))


@router.get(
    "/admin/toss/accounts/{account_seq}/orders/{order_id}",
    response_model=ApiEnvelope,
    tags=["admin", "toss", "orders"],
    dependencies=[Depends(require_admin_access)],
)
def get_toss_order_detail(
    account_seq: int = Path(gt=0),
    order_id: str = Path(pattern=r"^[a-zA-Z0-9_-]{1,128}$"),
    service: TossOpenApiService = Depends(get_toss_open_api_service),
):
    """실제 주문 상세와 부분 체결 상태를 읽기 전용으로 조회한다."""
    return envelope(service.order_detail(account_seq, order_id))


@router.get(
    "/admin/toss/accounts/{account_seq}/conditional-orders/{conditional_order_id}",
    response_model=ApiEnvelope,
    tags=["admin", "toss", "conditional-orders"],
    dependencies=[Depends(require_admin_access)],
)
def get_toss_conditional_order_detail(
    account_seq: int = Path(gt=0),
    conditional_order_id: str = Path(pattern=r"^[a-zA-Z0-9_-]{1,128}$"),
    service: TossOpenApiService = Depends(get_toss_open_api_service),
):
    """실제 조건주문의 감시·실행 상태를 읽기 전용으로 조회한다."""
    return envelope(service.conditional_order_detail(account_seq, conditional_order_id))


@router.post(
    "/admin/toss/accounts/{account_seq}/orders",
    response_model=ApiEnvelope,
    tags=["admin", "toss", "orders"],
    dependencies=[Depends(require_admin_access)],
)
def create_toss_order(
    request: TossOrderCreateRequest,
    account_seq: int = Path(gt=0),
    service: TossOpenApiService = Depends(get_toss_open_api_service),
):
    """`create_toss_order`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

    payload = request.model_dump(
        by_alias=True, exclude_none=True, exclude={"confirmation"}, mode="json"
    )
    return envelope(
        service.submit_order(account_seq, payload, confirmation=request.confirmation)
    )


@router.post(
    "/admin/toss/accounts/{account_seq}/orders/{order_id}/modify",
    response_model=ApiEnvelope,
    tags=["admin", "toss", "orders"],
    dependencies=[Depends(require_admin_access)],
)
def modify_toss_order(
    request: TossOrderModifyRequest,
    account_seq: int = Path(gt=0),
    order_id: str = Path(pattern=r"^[a-zA-Z0-9_-]{1,128}$"),
    service: TossOpenApiService = Depends(get_toss_open_api_service),
):
    """`modify_toss_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    payload = request.model_dump(
        by_alias=True, exclude_none=True, exclude={"confirmation"}, mode="json"
    )
    return envelope(
        service.modify_order(
            account_seq, order_id, payload, confirmation=request.confirmation
        )
    )


@router.post(
    "/admin/toss/accounts/{account_seq}/orders/{order_id}/cancel",
    response_model=ApiEnvelope,
    tags=["admin", "toss", "orders"],
    dependencies=[Depends(require_admin_access)],
)
def cancel_toss_order(
    request: TossMutationConfirmation,
    account_seq: int = Path(gt=0),
    order_id: str = Path(pattern=r"^[a-zA-Z0-9_-]{1,128}$"),
    service: TossOpenApiService = Depends(get_toss_open_api_service),
):
    """`cancel_toss_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return envelope(
        service.cancel_order(account_seq, order_id, confirmation=request.confirmation)
    )


@router.post(
    "/admin/toss/accounts/{account_seq}/conditional-orders",
    response_model=ApiEnvelope,
    tags=["admin", "toss", "conditional-orders"],
    dependencies=[Depends(require_admin_access)],
)
def create_toss_conditional_order(
    request: TossConditionalOrderRequest,
    account_seq: int = Path(gt=0),
    service: TossOpenApiService = Depends(get_toss_open_api_service),
):
    """`create_toss_conditional_order`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

    if request.symbol is None:
        raise HTTPException(status_code=422, detail="symbol is required when creating an order")
    payload = request.model_dump(
        by_alias=True, exclude_none=True, exclude={"confirmation"}, mode="json"
    )
    return envelope(
        service.submit_conditional_order(
            account_seq, payload, confirmation=request.confirmation
        )
    )


@router.post(
    "/admin/toss/accounts/{account_seq}/conditional-orders/{conditional_order_id}/modify",
    response_model=ApiEnvelope,
    tags=["admin", "toss", "conditional-orders"],
    dependencies=[Depends(require_admin_access)],
)
def modify_toss_conditional_order(
    request: TossConditionalOrderRequest,
    account_seq: int = Path(gt=0),
    conditional_order_id: str = Path(pattern=r"^[a-zA-Z0-9_-]{1,128}$"),
    service: TossOpenApiService = Depends(get_toss_open_api_service),
):
    """`modify_toss_conditional_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    payload = request.model_dump(
        by_alias=True,
        exclude_none=True,
        exclude={"confirmation", "symbol", "client_order_id"},
        mode="json",
    )
    return envelope(
        service.modify_conditional_order(
            account_seq,
            conditional_order_id,
            payload,
            confirmation=request.confirmation,
        )
    )


@router.delete(
    "/admin/toss/accounts/{account_seq}/conditional-orders/{conditional_order_id}",
    response_model=ApiEnvelope,
    tags=["admin", "toss", "conditional-orders"],
    dependencies=[Depends(require_admin_access)],
)
def cancel_toss_conditional_order(
    request: TossMutationConfirmation,
    account_seq: int = Path(gt=0),
    conditional_order_id: str = Path(pattern=r"^[a-zA-Z0-9_-]{1,128}$"),
    service: TossOpenApiService = Depends(get_toss_open_api_service),
):
    """`cancel_toss_conditional_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return envelope(
        service.cancel_conditional_order(
            account_seq,
            conditional_order_id,
            confirmation=request.confirmation,
        )
    )


@router.post("/backtests", response_model=ApiEnvelope, tags=["backtest"])
def run_backtest(
    request: BacktestRequest, service: BacktestService = Depends(get_backtest_service)
):
    """`run_backtest`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다."""

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
                corporate_action_mode=request.corporate_action_mode,
            )
        )
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CorporateActionAdjustmentUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/backtests/walk-forward",
    response_model=ApiEnvelope,
    tags=["backtest"],
)
def validate_backtest_walk_forward(
    request: BacktestValidationRequest,
    service: BacktestService = Depends(get_backtest_service),
):
    """`validate_backtest_walk_forward`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다."""

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
                corporate_action_mode=request.corporate_action_mode,
            )
        )
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CorporateActionAdjustmentUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get(
    "/admin/operations/status",
    response_model=ApiEnvelope,
    tags=["admin", "operations"],
    dependencies=[Depends(require_admin_access)],
)
async def get_operations_status(
    service: OperationsStatusService = Depends(get_operations_status_service),
):
    """`get_operations_status`은(는) 비동기로 필요한 데이터를 조회해 반환합니다."""

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
    """`get_data_quality_history`은(는) 필요한 데이터를 조회해 반환합니다."""

    return envelope(
        service.recent(
            limit=limit,
            offset=offset,
            symbol=symbol,
            severity=severity,
        )
    )


@router.get(
    "/admin/candles/price-basis-inventory",
    response_model=ApiEnvelope,
    tags=["admin", "operations", "data-pipeline"],
    dependencies=[Depends(require_admin_access)],
)
def get_candle_price_basis_inventory(
    symbol: str = Query(pattern=r"^[0-9A-Z.-]{1,16}$"),
    limit: int = Query(default=200, ge=1, le=500),
    service: CandlePriceBasisInventoryService = Depends(get_candle_price_basis_inventory_service),
):
    """`get_candle_price_basis_inventory`은(는) 필요한 데이터를 조회해 반환합니다."""

    return envelope(service.summarize(symbol=symbol, limit=limit))


@router.get(
    "/admin/ingestion",
    response_model=ApiEnvelope,
    tags=["admin", "operations", "data-pipeline"],
    dependencies=[Depends(require_admin_access)],
)
def get_ingestion_status(
    service: IngestionOperationsService = Depends(get_ingestion_operations_service),
):
    """`get_ingestion_status`은(는) 필요한 데이터를 조회해 반환합니다."""

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
    """`get_provider_audit_history`은(는) 필요한 데이터를 조회해 반환합니다."""

    return envelope(
        service.recent(
            limit=limit,
            offset=offset,
            provider=provider,
            outcome=outcome,
        )
    )


@router.post(
    "/admin/provider-audits/cleanup",
    response_model=ApiEnvelope,
    tags=["admin", "operations", "audit"],
    dependencies=[Depends(require_admin_access)],
)
def cleanup_provider_audit_history(
    service: ProviderAuditMaintenanceService = Depends(get_provider_audit_maintenance_service),
):
    """`cleanup_provider_audit_history`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다."""

    return envelope(service.cleanup())


@router.get(
    "/admin/data-lifecycle/preview",
    response_model=ApiEnvelope,
    tags=["admin", "operations", "data-lifecycle"],
    dependencies=[Depends(require_admin_access)],
)
def preview_data_lifecycle_cleanup(
    service: DataLifecycleMaintenanceService = Depends(get_data_lifecycle_maintenance_service),
):
    """`preview_data_lifecycle_cleanup`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return envelope(service.preview())


@router.post(
    "/admin/data-lifecycle/cleanup",
    response_model=ApiEnvelope,
    tags=["admin", "operations", "data-lifecycle"],
    dependencies=[Depends(require_admin_access)],
)
def cleanup_expired_operational_data(
    service: DataLifecycleMaintenanceService = Depends(get_data_lifecycle_maintenance_service),
):
    """`cleanup_expired_operational_data`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다."""

    return envelope(service.cleanup())


@router.get(
    "/admin/corporate-actions",
    response_model=ApiEnvelope,
    tags=["admin", "operations", "data-pipeline"],
    dependencies=[Depends(require_admin_access)],
)
def get_corporate_action_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    symbol: str | None = Query(default=None, pattern=r"^[0-9A-Z.-]{1,16}$"),
    as_of: datetime | None = Query(default=None),
    service: CorporateActionService = Depends(get_corporate_action_service),
):
    """`get_corporate_action_history`은(는) 필요한 데이터를 조회해 반환합니다."""

    try:
        return envelope(
            service.recent(
                limit=limit,
                offset=offset,
                symbol=symbol,
                as_of=as_of,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get(
    "/admin/corporate-actions/ingestion",
    response_model=ApiEnvelope,
    tags=["admin", "operations", "data-pipeline"],
    dependencies=[Depends(require_admin_access)],
)
def get_corporate_action_ingestion_status(
    service: CorporateActionIngestionService = Depends(get_corporate_action_ingestion_service),
):
    """`get_corporate_action_ingestion_status`은(는) 필요한 데이터를 조회해 반환합니다."""

    return envelope(service.status())


@router.get(
    "/admin/corporate-actions/candidates",
    response_model=ApiEnvelope,
    tags=["admin", "operations", "data-pipeline"],
    dependencies=[Depends(require_admin_access)],
)
def get_corporate_action_candidate_status(
    service: CorporateActionCandidateService = Depends(get_corporate_action_candidate_service),
):
    """`get_corporate_action_candidate_status`은(는) 필요한 데이터를 조회해 반환합니다."""

    return envelope(service.status())


@router.get(
    "/admin/corporate-actions/candidates/{source}/{symbol}",
    response_model=ApiEnvelope,
    tags=["admin", "operations", "data-pipeline"],
    dependencies=[Depends(require_admin_access)],
)
def preview_corporate_action_candidates(
    source: str = Path(pattern=r"^[a-z0-9_-]{1,32}$"),
    symbol: str = Path(pattern=r"^[0-9A-Z.-]{1,16}$"),
    start: date = Query(),
    end: date = Query(),
    limit: int = Query(default=100, ge=1, le=200),
    service: CorporateActionCandidateService = Depends(get_corporate_action_candidate_service),
):
    """`preview_corporate_action_candidates`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    try:
        return envelope(
            service.preview(
                source,
                symbol,
                start=start,
                end=end,
                limit=limit,
            )
        )
    except CorporateActionSourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get(
    "/admin/corporate-actions/approvals",
    response_model=ApiEnvelope,
    tags=["admin", "operations", "data-pipeline"],
    dependencies=[Depends(require_admin_access)],
)
def get_corporate_action_approval_status(
    service: CorporateActionApprovalService = Depends(get_corporate_action_approval_service),
):
    """`get_corporate_action_approval_status`은(는) 필요한 데이터를 조회해 반환합니다."""

    return envelope(service.status())


@router.post(
    "/admin/corporate-actions/approvals/{source}/{symbol}",
    response_model=ApiEnvelope,
    tags=["admin", "operations", "data-pipeline"],
    dependencies=[Depends(require_admin_access)],
)
def approve_corporate_action_candidate(
    request: CorporateActionApprovalRequest,
    source: str = Path(pattern=r"^[a-z0-9_-]{1,32}$"),
    symbol: str = Path(pattern=r"^[0-9A-Z.-]{1,16}$"),
    service: CorporateActionApprovalService = Depends(get_corporate_action_approval_service),
):
    """`approve_corporate_action_candidate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    try:
        return envelope(
            service.approve(
                source,
                symbol,
                start=request.start,
                end=request.end,
                group_hint=request.group_hint,
                receipt_no=request.receipt_no,
                effective_at=request.effective_at,
                exchange_evidence_url=request.exchange_evidence_url,
                confirmation=request.confirmation,
            )
        )
    except CorporateActionApprovalUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except CorporateActionSourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CorporateActionApprovalConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/admin/corporate-actions/ingestion/{source}/{symbol}",
    response_model=ApiEnvelope,
    tags=["admin", "operations", "data-pipeline"],
    dependencies=[Depends(require_admin_access)],
)
def trigger_corporate_action_ingestion(
    source: str = Path(pattern=r"^[a-z0-9_-]{1,32}$"),
    symbol: str = Path(pattern=r"^[0-9A-Z.-]{1,16}$"),
    start: datetime = Query(),
    end: datetime = Query(),
    limit: int = Query(default=200, ge=1, le=500),
    service: CorporateActionIngestionService = Depends(get_corporate_action_ingestion_service),
):
    """`trigger_corporate_action_ingestion`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    try:
        return envelope(
            service.ingest(
                source,
                symbol,
                start=start,
                end=end,
                limit=limit,
            )
        )
    except CorporateActionIngestionUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except CorporateActionSourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (
        CorporateActionRevisionConflictError,
        UntrustedCorporateActionSourceError,
    ) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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
    """`trigger_candle_ingestion`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
    """`get_backtest_history`은(는) 필요한 데이터를 조회해 반환합니다."""

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
    """`compare_backtest_engines`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
                corporate_action_mode=request.corporate_action_mode,
            )
        )
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CorporateActionAdjustmentUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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
    """`compare_backtest_strategies`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
                corporate_action_mode=request.corporate_action_mode,
            )
        )
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CorporateActionAdjustmentUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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
    """`get_backtest_history_detail`은(는) 필요한 데이터를 조회해 반환합니다."""

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
    """`get_model_versions`은(는) 필요한 데이터를 조회해 반환합니다."""

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
    """`promote_model_version`은(는) 기존 상태를 검증된 새 값으로 변경합니다."""

    try:
        return envelope(service.promote(version))
    except ModelRegistryUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ModelVersionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ModelArtifactValidationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get(
    "/admin/local-ai/readiness",
    response_model=ApiEnvelope,
    tags=["admin", "prediction"],
    dependencies=[Depends(require_admin_access)],
)
def get_local_ai_readiness(
    service: LocalAiReadinessService = Depends(get_local_ai_readiness_service),
):
    """직접 학습 AI의 artifact 무결성과 품질 게이트 상태를 조회한다."""

    return envelope(service.summary())


@router.get(
    "/admin/watchlist",
    response_model=ApiEnvelope,
    tags=["admin"],
    dependencies=[Depends(require_admin_access)],
)
def get_watchlist(
    service: ReferenceAlertService = Depends(get_reference_alert_service),
):
    """`get_watchlist`은(는) 필요한 데이터를 조회해 반환합니다."""

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
    """`add_watchlist_item`은(는) 데이터를 저장하거나 기존 상태에 추가합니다."""

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
    """`remove_watchlist_item`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다."""

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
    """`get_reference_alerts`은(는) 필요한 데이터를 조회해 반환합니다."""

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
    """`create_reference_alert`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

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
    """`evaluate_reference_alerts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
    """`disable_reference_alert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
    """`get_score`은(는) 필요한 데이터를 조회해 반환합니다."""

    try:
        return envelope(service.score(symbol, limit))
    except UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
