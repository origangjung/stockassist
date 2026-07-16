from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.backtest import BacktestConfig, BacktestEngine, CostModel
from app.indicators import IndicatorEngine
from app.providers.contracts import Candle
from app.score import ScoreEngine, TechnicalScoreCalculator
from app.score.strategy import TechnicalScoreStrategy
from app.adapters.broker import BrokerAdapter
from app.disclosures.providers import MockDisclosureProvider
from app.financials.providers import MockFinancialProvider
from app.investor_flow.providers import MockInvestorFlowProvider
from app.news.providers import MockNewsProvider
from app.providers.mock import MockProvider
from app.services.content import DisclosureAnalysisService, NewsAnalysisService
from app.services.financial import FinancialAnalysisService
from app.services.investor_flow import InvestorFlowService
from app.services.score import ScoreService


def trend_candles(direction: int, count: int = 40) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        Candle(
            start + timedelta(days=index),
            Decimal(100 + direction * index),
            Decimal(102 + direction * index),
            Decimal(98 + direction * index),
            Decimal(101 + direction * index),
            1_000,
        )
        for index in range(count)
    ]


def technical_score(candles: list[Candle]) -> float:
    indicators = IndicatorEngine().calculate(candles)
    score, _ = TechnicalScoreCalculator().calculate(candles[-1], indicators[-1])
    assert score is not None
    return score


def test_technical_score_distinguishes_rising_and_falling_golden_series():
    rising = technical_score(trend_candles(1))
    falling = technical_score(trend_candles(-1))
    assert rising == 56.8517
    assert falling == 27.3063
    assert rising - falling > 20


def test_partial_score_exposes_missing_axes_and_coverage():
    result = ScoreEngine().aggregate((60, ["golden technical evidence"]))
    assert result.overall_score == 60
    assert result.coverage_ratio == 0.3
    assert result.is_partial is True
    assert sum(axis.available for axis in result.axes) == 1
    assert result.validation_status == "experimental"


def test_score_strategy_runs_under_t_plus_one_backtest_rule():
    result = BacktestEngine().run(
        trend_candles(1),
        TechnicalScoreStrategy(threshold=50),
        BacktestConfig(initial_capital=1_000, force_close=False, costs=CostModel(0, 0, 0)),
    )
    assert result.equity_curve[0].position == 0
    assert result.strategy == "technical_score_50"


def test_score_service_connects_all_six_available_axes():
    broker = BrokerAdapter([MockProvider()])
    result = ScoreService(
        broker,
        IndicatorEngine(),
        TechnicalScoreCalculator(),
        ScoreEngine(),
        financial=FinancialAnalysisService(MockFinancialProvider()),
        news=NewsAnalysisService(MockNewsProvider()),
        disclosure=DisclosureAnalysisService(MockDisclosureProvider()),
        investor_flow=InvestorFlowService(MockInvestorFlowProvider()),
    ).score("005930", 60)

    assert result["coverage_ratio"] == 1.0
    assert result["is_partial"] is False
    assert len(result["axes"]) == 6
    assert all(axis["available"] for axis in result["axes"])
    assert 0 <= result["overall_score"] <= 100


def test_score_analysis_bundle_retains_exact_source_facts_for_agents():
    service = ScoreService(
        BrokerAdapter([MockProvider()]),
        IndicatorEngine(),
        TechnicalScoreCalculator(),
        ScoreEngine(),
        financial=FinancialAnalysisService(MockFinancialProvider()),
        news=NewsAnalysisService(MockNewsProvider()),
        disclosure=DisclosureAnalysisService(MockDisclosureProvider()),
        investor_flow=InvestorFlowService(MockInvestorFlowProvider()),
    )

    bundle = service.analysis_bundle("005930", 60)

    assert bundle.score["coverage_ratio"] == 1.0
    assert bundle.source_status == {
        "technical": "available",
        "financial": "available",
        "news": "available",
        "disclosure": "available",
        "investor_flow": "available",
        "market_risk": "available",
    }
    assert bundle.source_facts["investor_flow"]["symbol"] == "005930"
    assert bundle.candles[-1].timestamp == bundle.score["data_as_of"]


def test_score_service_isolates_optional_axis_failure():
    class FailingFinancialService:
        def snapshot(self, symbol: str, fiscal_year: int):
            raise TimeoutError(f"{symbol}:{fiscal_year}")

    result = ScoreService(
        BrokerAdapter([MockProvider()]),
        IndicatorEngine(),
        TechnicalScoreCalculator(),
        ScoreEngine(),
        financial=FailingFinancialService(),
    ).score("005930", 60)

    axes = {axis["axis"]: axis for axis in result["axes"]}
    assert axes["technical"]["available"] is True
    assert axes["market_risk"]["available"] is True
    assert axes["financial"]["available"] is False
    assert axes["financial"]["evidence"] == ["데이터 조회 실패 (TimeoutError)"]
    assert result["coverage_ratio"] == 0.45
