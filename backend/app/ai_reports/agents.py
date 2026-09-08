"""agents 파일은 백엔드 도메인 기능을 담당한다."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from typing import Any

from app.microstructure import calculate_market_pressure
from app.patterns import PatternEngine
from app.providers.contracts import Candle
from app.providers.errors import ProviderError
from app.services.investor_flow import InvestorFlowService
from app.services.market import MarketDataService
from app.services.prediction import PredictionService
from app.services.score import ScoreAnalysisBundle, ScoreService
from app.local_ai.market_features import latest_market_features


@dataclass(frozen=True)
class AgentFinding:
    """전문 분석 과정에서 확인한 결과와 근거를 묶어 전달합니다."""

    name: str
    status: str
    evidence: list[str]
    data_as_of: datetime | None = None
    value: Any = None

    def to_dict(self) -> dict[str, Any]:
        """`to_dict`은(는) 내부 값을 전송·표시 가능한 형식으로 변환합니다."""

        return asdict(self)


@dataclass
class AnalysisContext:
    """여러 처리 단계가 함께 사용하는 실행 문맥과 입력 정보를 묶습니다."""

    symbol: str
    horizon_days: int
    limit: int
    facts: dict[str, Any] = field(default_factory=dict)
    score_bundle: ScoreAnalysisBundle | None = None
    candles: list[Candle] | None = None


class AnalysisAgent(ABC):
    """`AnalysisAgent` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    name: str

    @abstractmethod
    def analyze(self, context: AnalysisContext) -> AgentFinding:
        """Return bounded structured evidence without generating prose."""


class ScoreAnalysisAgent(AnalysisAgent):
    """`ScoreAnalysisAgent` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    name = "score"

    def __init__(self, service: ScoreService, market: MarketDataService) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._service = service
        self._market = market

    def analyze(self, context: AnalysisContext) -> AgentFinding:
        """`analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다."""

        bundle = self._service.analysis_bundle(context.symbol, context.limit)
        context.score_bundle = bundle
        context.facts["score"] = bundle.score
        benchmark_candles = None
        if not context.symbol.isdigit():
            try:
                benchmark_symbol = "VTI" if context.symbol.upper() == "SPY" else "SPY"
                benchmark_candles, _provider = self._market.candles(
                    benchmark_symbol, context.limit
                )
            except (ProviderError, ValueError):
                benchmark_candles = None
        context.facts["local_market_features"] = latest_market_features(
            bundle.candles, benchmark_candles
        )
        return AgentFinding(
            self.name,
            "available",
            [
                f"six-axis coverage={bundle.score.get('coverage_ratio')}",
                f"weight_version={bundle.score.get('weight_version')}",
            ],
            bundle.score.get("data_as_of"),
            bundle.score.get("overall_score"),
        )


class ScoreAxisAgent(AnalysisAgent):
    """`ScoreAxisAgent` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    def __init__(self, axis: str) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self.name = axis
        self._axis = axis

    def analyze(self, context: AnalysisContext) -> AgentFinding:
        """`analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다."""

        bundle = context.score_bundle
        if bundle is None:
            return AgentFinding(self.name, "unavailable", ["score bundle unavailable"])
        axis = next(
            (item for item in bundle.score.get("axes", []) if item.get("axis") == self._axis),
            None,
        )
        if not isinstance(axis, dict):
            return AgentFinding(self.name, "unavailable", ["axis result unavailable"])
        status = "available" if axis.get("available") else "unavailable"
        evidence = [str(item) for item in axis.get("evidence", [])]
        provider = (
            bundle.score.get("provider")
            if self._axis == "technical"
            else _provider_name(bundle.source_facts.get(self._axis))
        )
        value = {
            "score": axis.get("score"),
            "weight": axis.get("weight"),
            "provider": provider,
        }
        return AgentFinding(
            self.name,
            status,
            evidence,
            bundle.score.get("data_as_of"),
            value,
        )


class PredictionAnalysisAgent(AnalysisAgent):
    """`PredictionAnalysisAgent` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    name = "prediction"

    def __init__(self, service: PredictionService) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._service = service

    def analyze(self, context: AnalysisContext) -> AgentFinding:
        """`analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다."""

        prediction = self._service.predict(
            context.symbol,
            horizon_days=context.horizon_days,
            limit=context.limit,
        )
        context.facts["prediction"] = prediction
        evidence = [
            f"model_version={prediction.get('model_version')}",
            f"horizon_days={prediction.get('horizon_days')}",
        ]
        return AgentFinding(
            self.name,
            "available",
            evidence,
            prediction.get("data_as_of"),
            {
                "rise_probability": prediction.get("rise_probability"),
                "confidence_lower": prediction.get("confidence_lower"),
                "confidence_upper": prediction.get("confidence_upper"),
            },
        )


class RiskAnalysisAgent(AnalysisAgent):
    """`RiskAnalysisAgent` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    name = "risk"

    def __init__(self, market: MarketDataService) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._market = market

    def analyze(self, context: AnalysisContext) -> AgentFinding:
        """`analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다."""

        bundle = context.score_bundle
        if bundle is not None and bundle.source_status.get("market_risk") == "available":
            warnings = bundle.source_facts.get("market_risk") or []
        else:
            warnings, _provider = self._market.warnings(context.symbol)
        serialized = [_mapping(item) for item in warnings]
        context.facts["warnings"] = serialized
        warning_types = [str(item.get("warning_type", "unknown")) for item in serialized]
        return AgentFinding(
            self.name,
            "available",
            [f"active_warning_count={len(serialized)}", *warning_types[:3]],
            value={"warning_count": len(serialized), "warning_types": warning_types},
        )


class InvestorFlowAnalysisAgent(AnalysisAgent):
    """`InvestorFlowAnalysisAgent` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    name = "investor_flow"

    def __init__(self, service: InvestorFlowService) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._service = service

    def analyze(self, context: AnalysisContext) -> AgentFinding:
        """`analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다."""

        bundle = context.score_bundle
        if bundle is not None and bundle.source_status.get(self.name) == "available":
            snapshot = bundle.source_facts[self.name]
        else:
            snapshot = self._service.snapshot(context.symbol)
        context.facts[self.name] = snapshot
        return AgentFinding(
            self.name,
            "available",
            [f"reference_signal={snapshot.get('reference_signal')}"],
            snapshot.get("data_as_of"),
            {
                "foreign_institution_net_quantity": snapshot.get(
                    "foreign_institution_net_quantity"
                ),
                "reference_signal": snapshot.get("reference_signal"),
                "provider": snapshot.get("provider"),
            },
        )


class ChartPatternAnalysisAgent(AnalysisAgent):
    """`ChartPatternAnalysisAgent` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    name = "chart_pattern"

    def __init__(self, market: MarketDataService, engine: PatternEngine) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._market = market
        self._engine = engine

    def analyze(self, context: AnalysisContext) -> AgentFinding:
        """`analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다."""

        if context.score_bundle is not None:
            candles = context.score_bundle.candles
        elif context.candles is not None:
            candles = context.candles
        else:
            candles, _provider = self._market.candles(context.symbol, context.limit)
            context.candles = candles
        result = self._engine.analyze(candles)
        context.facts["chart_patterns"] = result
        patterns = result["patterns"]
        evidence = [
            f"{item['name']}:{item['direction']}:{item['confidence']:.2f}" for item in patterns[:5]
        ] or ["no active chart or candlestick pattern"]
        evidence.extend(
            f"{item['pattern_name']}:10d_spy_relative_underperformance_watch"
            for item in result.get("reference_signals", [])
        )
        return AgentFinding(
            self.name,
            "available",
            evidence,
            result.get("data_as_of"),
            result,
        )


class MarketPressureAnalysisAgent(AnalysisAgent):
    """실시간 호가와 최근 체결로 어느 주문 방향이 우세한지 계산한다."""

    name = "market_pressure"

    def __init__(self, market: MarketDataService) -> None:
        """시장 데이터 서비스를 저장한다."""

        self._market = market

    def analyze(self, context: AnalysisContext) -> AgentFinding:
        """호가 불균형과 체결 방향을 결합한 단기 압력을 반환한다."""

        asks, bids, book_provider = self._market.orderbook(context.symbol)
        trades, trade_provider = self._market.trades(context.symbol, 50)
        result = {
            **calculate_market_pressure(asks, bids, trades),
            "provider": (
                book_provider
                if book_provider == trade_provider
                else f"{book_provider}+{trade_provider}"
            ),
        }
        context.facts[self.name] = result
        latest_trade = max(
            (trade.executed_at for trade in trades),
            default=None,
        )
        return AgentFinding(
            self.name,
            "available" if result["signal"] != "unavailable" else "unavailable",
            [
                f"signal={result['signal']}",
                f"pressure_score={float(result['score']):.4f}",
                f"source={result['source']}",
            ],
            latest_trade,
            result,
        )


class SupportResistanceAnalysisAgent(AnalysisAgent):
    """`SupportResistanceAnalysisAgent` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    name = "support_resistance"

    def __init__(self, market: MarketDataService) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._market = market

    def analyze(self, context: AnalysisContext) -> AgentFinding:
        """`analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다."""

        if context.score_bundle is not None:
            candles = context.score_bundle.candles[-20:]
        elif context.candles is not None:
            candles = context.candles[-20:]
        else:
            candles, _provider = self._market.candles(context.symbol, min(context.limit, 60))
            context.candles = candles
            candles = candles[-20:]
        if not candles:
            context.facts[self.name] = None
            return AgentFinding(self.name, "unavailable", ["candle window unavailable"])
        result = {
            "method": "trailing_20_candle_range",
            "support": min(candle.low for candle in candles),
            "resistance": max(candle.high for candle in candles),
            "status": "experimental",
        }
        context.facts[self.name] = result
        return AgentFinding(
            self.name,
            "available",
            [f"trailing_candle_count={len(candles)}"],
            candles[-1].timestamp,
            result,
        )


class MasterAnalysisOrchestrator:
    """Runs bounded agents and isolates optional-agent failures."""

    _axis_names = ("technical", "financial", "news", "disclosure")

    def __init__(
        self,
        market: MarketDataService,
        score: ScoreService,
        prediction: PredictionService,
        investor_flow: InvestorFlowService,
    ) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._market = market
        self._score_agent = ScoreAnalysisAgent(score, market)
        self._axis_agents = [ScoreAxisAgent(name) for name in self._axis_names]
        self._agents: list[AnalysisAgent] = [
            PredictionAnalysisAgent(prediction),
            RiskAnalysisAgent(market),
            InvestorFlowAnalysisAgent(investor_flow),
            ChartPatternAnalysisAgent(market, PatternEngine()),
            MarketPressureAnalysisAgent(market),
            SupportResistanceAnalysisAgent(market),
        ]

    def collect(
        self, symbol: str, *, horizon_days: int, limit: int
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """`collect`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        stock, provider = self._market.stock_info(symbol)
        context = AnalysisContext(symbol, horizon_days, limit)
        context.facts.update({"symbol": symbol, "stock": {**stock.__dict__, "provider": provider}})
        findings: dict[str, dict[str, Any]] = {}

        self._run(self._score_agent, context, findings)
        for agent in self._axis_agents:
            self._run(agent, context, findings)
        for agent in self._agents:
            self._run(agent, context, findings)

        context.facts.setdefault("score", None)
        context.facts.setdefault("prediction", None)
        context.facts.setdefault("warnings", [])
        context.facts.setdefault("investor_flow", None)
        context.facts.setdefault("chart_patterns", None)
        context.facts.setdefault("market_pressure", None)
        context.facts.setdefault("support_resistance", None)
        context.facts["agent_findings"] = findings
        status = {name: finding["status"] for name, finding in findings.items()}
        return context.facts, status

    @staticmethod
    def _run(
        agent: AnalysisAgent,
        context: AnalysisContext,
        findings: dict[str, dict[str, Any]],
    ) -> None:
        """`_run`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        try:
            finding = agent.analyze(context)
        except (ProviderError, ValueError) as exc:
            finding = AgentFinding(
                agent.name,
                "unavailable",
                [f"{type(exc).__name__}: analysis unavailable"],
            )
        findings[agent.name] = finding.to_dict()


def _mapping(value: Any) -> dict[str, Any]:
    """`_mapping`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if isinstance(value, dict):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    return {"value": str(value)}


def _provider_name(value: Any) -> str | None:
    """`_provider_name`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return str(value.get("provider")) if isinstance(value, dict) and value.get("provider") else None
