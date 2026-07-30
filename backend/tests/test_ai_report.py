from datetime import datetime, timezone
import json

import httpx2
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.adapters.broker import BrokerAdapter
from app.ai_reports.compliance import ComplianceValidator
from app.ai_reports.errors import ReportComplianceError
from app.ai_reports.mock import MockAIReportGenerator
from app.ai_reports.openai import OpenAIReportGenerator
from app.models.ai_report import AIReportModel
from app.repositories.sqlalchemy import SqlAlchemyAIReportRepository
from app.indicators import IndicatorEngine
from app.investor_flow.providers import MockInvestorFlowProvider
from app.prediction import LightweightPredictionEngine
from app.providers.mock import MockProvider
from app.repositories.memory import InMemoryAIReportRepository
from app.score import ScoreEngine, TechnicalScoreCalculator
from app.services.ai_report import AIReportService
from app.services.investor_flow import InvestorFlowService
from app.services.market import MarketDataService
from app.services.prediction import PredictionService
from app.services.score import ScoreService


def _service(repository=None):
    broker = BrokerAdapter([MockProvider()])
    return AIReportService(
        MarketDataService(broker),
        ScoreService(broker, IndicatorEngine(), TechnicalScoreCalculator(), ScoreEngine()),
        PredictionService(broker, LightweightPredictionEngine()),
        InvestorFlowService(MockInvestorFlowProvider()),
        MockAIReportGenerator(),
        ComplianceValidator(),
        repository,
    )


def test_ai_report_is_experimental_and_persists_only_after_compliance_passes():
    repository = InMemoryAIReportRepository()
    report = _service(repository).report("005930", horizon_days=5, limit=180)

    assert report["generator"] == "mock"
    assert report["validation_status"] == "experimental"
    assert report["is_investment_advice"] is False
    assert report["reference_signal"] == "positive_watch"
    assert report["signal_strength"] > 0
    assert len(report["signal_basis"]) == 3
    assert report["persistence_status"] == "saved"
    assert report["model_version"] == "ai-report-2026.3"
    assert report["agent_status"]["technical"] == "available"
    assert report["agent_status"]["chart_pattern"] == "available"
    assert report["agent_status"]["risk"] == "available"
    assert report["agent_findings"]["prediction"]["value"]["rise_probability"] is not None
    assert report["chart_patterns"]["engine_version"] == "patterns-2026.1"
    assert len(repository.items) == 1


def test_ai_report_reuses_score_candles_and_warning_facts():
    class CountingMockProvider(MockProvider):
        def __init__(self):
            super().__init__()
            self.candle_calls = 0
            self.warning_calls = 0

        def get_candles(self, symbol: str, limit: int):
            self.candle_calls += 1
            return super().get_candles(symbol, limit)

        def get_warnings(self, symbol: str):
            self.warning_calls += 1
            return super().get_warnings(symbol)

    provider = CountingMockProvider()
    broker = BrokerAdapter([provider])
    service = AIReportService(
        MarketDataService(broker),
        ScoreService(broker, IndicatorEngine(), TechnicalScoreCalculator(), ScoreEngine()),
        PredictionService(broker, LightweightPredictionEngine()),
        InvestorFlowService(MockInvestorFlowProvider()),
        MockAIReportGenerator(),
        ComplianceValidator(),
    )

    service.report("005930", horizon_days=5, limit=180)

    # Score and prediction each need candles; support/resistance reuses the score window.
    assert provider.candle_calls == 2
    assert provider.warning_calls == 1


def test_sqlalchemy_ai_report_persistence_encodes_decimal_json_values():
    engine = create_engine("sqlite://")
    AIReportModel.__table__.create(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)

    try:
        report = _service(SqlAlchemyAIReportRepository(sessions)).report(
            "005930", horizon_days=5, limit=180
        )
        with sessions() as session:
            stored = session.scalar(select(AIReportModel))

        assert stored is not None
        assert stored.report["rise_probability"] == str(report["rise_probability"])
        assert stored.report["support_resistance"]["support"] == str(
            report["support_resistance"]["support"]
        )
        assert stored.report["data_as_of"] == report["data_as_of"].isoformat()
    finally:
        engine.dispose()


def test_master_orchestrator_isolates_score_agent_failure():
    class FailingScoreService:
        def analysis_bundle(self, symbol: str, limit: int):
            raise ValueError(f"score unavailable: {symbol}:{limit}")

    broker = BrokerAdapter([MockProvider()])
    report = AIReportService(
        MarketDataService(broker),
        FailingScoreService(),
        PredictionService(broker, LightweightPredictionEngine()),
        InvestorFlowService(MockInvestorFlowProvider()),
        MockAIReportGenerator(),
        ComplianceValidator(),
    ).report("005930", horizon_days=5, limit=180)

    assert report["agent_status"]["score"] == "unavailable"
    assert report["agent_status"]["technical"] == "unavailable"
    assert report["agent_status"]["prediction"] == "available"
    assert report["agent_status"]["risk"] == "available"
    assert report["agent_status"]["support_resistance"] == "available"
    assert report["overall_score"] is None


def test_compliance_validator_blocks_trading_instructions():
    report = {
        "summary": "You should buy this stock now.",
        "disclaimer": "reference only",
        "data_as_of": datetime.now(timezone.utc),
        "is_investment_advice": False,
        "reference_signal": "neutral_watch",
    }

    with pytest.raises(ReportComplianceError, match="trading instruction"):
        ComplianceValidator().validate(report)

    report["summary"] = "\uc9c0\uae08 \ub9e4\uc218\ud558\uc138\uc694."
    with pytest.raises(ReportComplianceError, match="trading instruction"):
        ComplianceValidator().validate(report)


def test_openai_generator_requests_strict_structured_output():
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.headers["Authorization"] == "Bearer test-key"
        body = json.loads(request.content)
        assert body["text"]["format"]["type"] == "json_schema"
        assert body["text"]["format"]["strict"] is True
        return httpx2.Response(
            200,
            json={
                "output": [
                    {
                        "content": [
                            {
                                "type": "output_text",
                                "text": '{"summary":"Neutral summary.","key_points":["Point."],'
                                '"risk_factors":["Risk."],"counterpoints":["Counterpoint."]}',
                            }
                        ]
                    }
                ]
            },
        )

    generator = OpenAIReportGenerator(
        api_key="test-key",
        base_url="https://example.test/v1",
        model="gpt-5",
        timeout_seconds=5,
        transport=httpx2.MockTransport(handler),
    )
    try:
        report = generator.generate({"symbol": "005930"})
    finally:
        generator.close()

    assert report["summary"] == "Neutral summary."
