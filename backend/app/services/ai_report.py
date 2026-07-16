from datetime import datetime, timezone
from decimal import Decimal

from app.ai_reports.agents import MasterAnalysisOrchestrator
from app.ai_reports.compliance import ComplianceValidator
from app.ai_reports.contracts import AIReportGenerator
from app.ai_reports.signals import derive_reference_signal
from app.core.compliance import DISCLAIMER
from app.repositories.contracts import AIReportRepository
from app.services.investor_flow import InvestorFlowService
from app.services.market import MarketDataService
from app.services.prediction import PredictionService
from app.services.score import ScoreService


REPORT_VERSION = "ai-report-2026.3"


class AIReportService:
    """Coordinates bounded analysis agents; only the generator writes prose."""

    def __init__(
        self,
        market: MarketDataService,
        score: ScoreService,
        prediction: PredictionService,
        investor_flow: InvestorFlowService,
        generator: AIReportGenerator,
        validator: ComplianceValidator,
        repository: AIReportRepository | None = None,
    ) -> None:
        self._generator = generator
        self._validator = validator
        self._repository = repository
        self._orchestrator = MasterAnalysisOrchestrator(
            market,
            score,
            prediction,
            investor_flow,
        )

    def report(self, symbol: str, *, horizon_days: int, limit: int) -> dict:
        facts, status = self._collect_facts(symbol, horizon_days=horizon_days, limit=limit)
        generated = self._generator.generate(facts)
        data_as_of = _latest_as_of(facts) or datetime.now(timezone.utc)
        warnings = facts.get("warnings") or []
        missing = [name for name, state in status.items() if state != "available"]
        signal = derive_reference_signal(
            facts.get("score"),
            facts.get("prediction"),
            warnings,
        )
        report = {
            "symbol": symbol,
            "generator": self._generator.name,
            "llm_model": self._generator.model,
            "model_version": REPORT_VERSION,
            "validation_status": "experimental",
            "overall_score": _value(facts.get("score"), "overall_score"),
            "rise_probability": _value(facts.get("prediction"), "rise_probability"),
            "downside_risk": "high" if warnings else "medium" if missing else "low",
            "reference_signal": signal.signal,
            "signal_strength": signal.strength,
            "signal_basis": signal.basis,
            "confidence": _confidence(facts.get("prediction")),
            "score_coverage": _value(facts.get("score"), "coverage_ratio"),
            "prediction_horizon_days": _value(facts.get("prediction"), "horizon_days"),
            "summary": _required_text(generated, "summary"),
            "key_points": _required_text_list(generated, "key_points"),
            "risk_factors": _required_text_list(generated, "risk_factors"),
            "counterpoints": _required_text_list(generated, "counterpoints"),
            "chart_patterns": facts.get("chart_patterns"),
            "support_resistance": facts.get("support_resistance"),
            "risk_warnings": warnings,
            "agent_status": status,
            "agent_findings": facts.get("agent_findings", {}),
            "data_as_of": data_as_of,
            "disclaimer": DISCLAIMER,
            "is_investment_advice": False,
            "compliance_status": "passed",
        }
        self._validator.validate(report)
        if self._repository is not None:
            self._repository.save(report)
        report["persistence_status"] = "saved" if self._repository is not None else "disabled"
        return report

    def _collect_facts(self, symbol: str, *, horizon_days: int, limit: int) -> tuple[dict, dict]:
        return self._orchestrator.collect(
            symbol,
            horizon_days=horizon_days,
            limit=limit,
        )


def _latest_as_of(facts: dict) -> datetime | None:
    candidates: list[datetime] = []
    for source in (facts.get("score"), facts.get("prediction"), facts.get("investor_flow")):
        value = _value(source, "data_as_of")
        if isinstance(value, datetime):
            candidates.append(value)
    return max(candidates) if candidates else None


def _value(source: dict | None, name: str):
    return source.get(name) if isinstance(source, dict) else None


def _confidence(prediction: dict | None) -> str:
    if not isinstance(prediction, dict):
        return "low"
    lower, upper = prediction.get("confidence_lower"), prediction.get("confidence_upper")
    if not isinstance(lower, (float, Decimal)) or not isinstance(upper, (float, Decimal)):
        return "low"
    width = float(upper) - float(lower)
    return "high" if width <= 0.15 else "medium" if width <= 0.30 else "low"


def _required_text(generated: dict, key: str) -> str:
    value = generated.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"AI report generator omitted {key}")
    return value.strip()


def _required_text_list(generated: dict, key: str) -> list[str]:
    value = generated.get(key)
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item.strip() for item in value)
    ):
        raise ValueError(f"AI report generator omitted {key}")
    return [item.strip() for item in value]
