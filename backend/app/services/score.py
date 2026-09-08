"""score 파일은 애플리케이션 사용 사례 기능을 담당한다."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import logging
from collections.abc import Callable
from typing import Any

from app.adapters.broker import BrokerAdapter
from app.indicators import IndicatorEngine
from app.pipeline.candles import CandlePipeline
from app.providers.contracts import Capability
from app.score import (
    ScoreEngine,
    TechnicalScoreCalculator,
    disclosure_axis,
    financial_axis,
    investor_flow_axis,
    market_risk_axis,
    news_axis,
)
from app.score.axes import AxisInput, unavailable_axis
from app.repositories.contracts import ScoreWeightRepository
from app.services.content import DisclosureAnalysisService, NewsAnalysisService
from app.services.financial import FinancialAnalysisService
from app.services.investor_flow import InvestorFlowService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScoreAnalysisBundle:
    """Internal score result plus the exact source facts used to calculate it."""

    score: dict[str, Any]
    source_facts: dict[str, Any]
    source_status: dict[str, str]
    candles: list[Any]


class ScoreService:
    """사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다."""

    def __init__(
        self,
        broker: BrokerAdapter,
        indicators: IndicatorEngine,
        technical: TechnicalScoreCalculator,
        score_engine: ScoreEngine,
        weights: ScoreWeightRepository | None = None,
        *,
        financial: FinancialAnalysisService | None = None,
        news: NewsAnalysisService | None = None,
        disclosure: DisclosureAnalysisService | None = None,
        investor_flow: InvestorFlowService | None = None,
    ):
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._broker = broker
        self._indicators = indicators
        self._technical = technical
        self._score_engine = score_engine
        self._weights = weights
        self._financial = financial
        self._news = news
        self._disclosure = disclosure
        self._investor_flow = investor_flow
        self._pipeline = CandlePipeline()

    def score(self, symbol: str, limit: int) -> dict:
        """`score`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        return self.analysis_bundle(symbol, limit).score

    def analysis_bundle(self, symbol: str, limit: int) -> ScoreAnalysisBundle:
        """`analysis_bundle`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        batch = self._broker.candles(symbol, limit)
        candles = self._pipeline.process(batch.candles).cleaned_candles
        indicator_rows = self._indicators.calculate(candles)
        engine = (
            ScoreEngine(self._weights.get_active())
            if self._weights is not None
            else self._score_engine
        )
        previous_fiscal_year = datetime.now(timezone.utc).year - 1
        source_facts: dict[str, Any] = {}
        source_status: dict[str, str] = {"technical": "available"}
        additional_inputs = {
            "financial": self._load_source_axis(
                "financial",
                None
                if self._financial is None
                else lambda: self._financial.snapshot(symbol, previous_fiscal_year),
                financial_axis,
                source_facts,
                source_status,
            ),
            "news": self._load_source_axis(
                "news",
                None if self._news is None else lambda: self._news.latest(symbol, limit=20),
                news_axis,
                source_facts,
                source_status,
            ),
            "disclosure": self._load_source_axis(
                "disclosure",
                None
                if self._disclosure is None
                else lambda: self._disclosure.latest(symbol, days=90, limit=20),
                disclosure_axis,
                source_facts,
                source_status,
            ),
            "investor_flow": self._load_source_axis(
                "investor_flow",
                None
                if self._investor_flow is None
                else lambda: self._investor_flow.snapshot(symbol),
                investor_flow_axis,
                source_facts,
                source_status,
            ),
            "market_risk": self._load_source_axis(
                "market_risk",
                lambda: self._broker.provider_for(Capability.WARNINGS).get_warnings(symbol),
                market_risk_axis,
                source_facts,
                source_status,
            ),
        }
        result = engine.aggregate(
            self._technical.calculate(candles[-1], indicator_rows[-1]),
            additional_inputs,
        )
        score = {
            "symbol": symbol,
            "provider": batch.provider.name,
            "data_as_of": candles[-1].timestamp,
            **asdict(result),
        }
        return ScoreAnalysisBundle(score, source_facts, source_status, candles)

    @classmethod
    def _load_source_axis(
        cls,
        name: str,
        loader: Callable[[], Any] | None,
        calculator: Callable[[Any], AxisInput],
        source_facts: dict[str, Any],
        source_status: dict[str, str],
    ) -> AxisInput:
        """`_load_source_axis`은(는) 필요한 데이터를 조회해 반환합니다."""

        if loader is None:
            source_facts[name] = None
            source_status[name] = "unavailable"
            return cls._load_axis(name, None)
        try:
            facts = loader()
            source_facts[name] = facts
            source_status[name] = "available"
            return calculator(facts)
        except Exception as exc:
            source_facts[name] = None
            source_status[name] = "unavailable"
            logger.warning(
                "Score source unavailable axis=%s error_type=%s",
                name,
                type(exc).__name__,
            )
            return unavailable_axis(f"데이터 조회 실패 ({type(exc).__name__})")

    @staticmethod
    def _load_axis(name: str, loader: Callable[[], AxisInput] | None) -> AxisInput:
        """`_load_axis`은(는) 필요한 데이터를 조회해 반환합니다."""

        if loader is None:
            return unavailable_axis("해당 데이터 서비스가 구성되지 않았습니다.")
        try:
            return loader()
        except Exception as exc:
            logger.warning(
                "Score axis unavailable axis=%s error_type=%s",
                name,
                type(exc).__name__,
            )
            return unavailable_axis(f"데이터 조회 실패 ({type(exc).__name__})")
