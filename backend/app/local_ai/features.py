"""features 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from typing import Any

from app.local_ai.contracts import AgentName
from app.local_ai.etf import ETF_ASSET_CLASS_FEATURES
from app.local_ai.flow_features import FLOW_FEATURES
from app.local_ai.flow_market_features import FLOW_MARKET_FEATURES, flow_market_features
from app.local_ai.financial_features import FINANCIAL_FEATURES
from app.local_ai.macro_features import MACRO_FEATURES
from app.local_ai.news_features import NEWS_FEATURES
from app.local_ai.market_features import (
    BENCHMARK_TECHNICAL_FEATURES,
    RISK_FEATURES,
    TECHNICAL_FEATURES,
)


FEATURES: dict[AgentName, tuple[str, ...]] = {
    "technical": TECHNICAL_FEATURES,
    "financial": FINANCIAL_FEATURES,
    "news": (*NEWS_FEATURES, *MACRO_FEATURES),
    "investor_flow": (*FLOW_FEATURES, *FLOW_MARKET_FEATURES),
    "risk": (*RISK_FEATURES, *MACRO_FEATURES),
}

ETF_MODEL_FEATURES = {
    "etf_technical": (
        *TECHNICAL_FEATURES,
        *BENCHMARK_TECHNICAL_FEATURES,
        *MACRO_FEATURES,
        *ETF_ASSET_CLASS_FEATURES,
    ),
    "etf_risk": (*RISK_FEATURES, *MACRO_FEATURES),
}

TARGETS: dict[AgentName, str] = {
    "technical": "future_positive_return",
    "financial": "future_fundamental_improvement",
    "news": "future_news_tone_improvement",
    "investor_flow": "future_short_pressure_increase",
    "risk": "future_downside_event",
}

SYNTHESIS_FEATURES = tuple(
    feature
    for agent in FEATURES
    for feature in (
        f"{agent}_probability",
        f"{agent}_confidence",
        f"{agent}_available",
    )
)

ETF_SYNTHESIS_FEATURES = (
    "technical_probability",
    "technical_confidence",
    "risk_probability",
    "risk_confidence",
    *MACRO_FEATURES,
)


def build_synthesis_features(results: dict[str, dict]) -> dict[str, float]:
    """`build_synthesis_features`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

    values: dict[str, float] = {}
    for agent in FEATURES:
        result = results.get(agent) or {}
        available = result.get("status") == "available"
        values[f"{agent}_probability"] = float(result.get("probability") or 0.5)
        values[f"{agent}_confidence"] = float(result.get("confidence") or 0.0)
        values[f"{agent}_available"] = float(available)
    return values


def build_etf_synthesis_features(
    results: dict[str, dict], macro_features: dict[str, float] | None
) -> dict[str, float] | None:
    """`build_etf_synthesis_features`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

    values: dict[str, float] = {}
    for agent in ("technical", "risk"):
        result = results.get(agent) or {}
        values[f"{agent}_probability"] = float(result.get("probability") or 0.5)
        values[f"{agent}_confidence"] = float(result.get("confidence") or 0.0)
    macro = _select(MACRO_FEATURES, macro_features or {})
    return {**values, **macro} if macro is not None else None


def extract_features(agent: AgentName, facts: dict[str, Any]) -> dict[str, float] | None:
    """`extract_features`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    market_features = facts.get("local_market_features") or {}
    if agent == "technical":
        return _select(TECHNICAL_FEATURES, market_features)
    if agent == "risk":
        risk_values = {
            name: market_features.get(f"risk_{name}") for name in RISK_FEATURES
        }
        risk_values.update(facts.get("local_macro_features") or {})
        return _select(FEATURES["risk"], risk_values)
    if agent == "financial":
        return _select(FINANCIAL_FEATURES, facts.get("local_financial_features") or {})
    if agent == "news":
        news_values = {
            **(facts.get("local_news_features") or {}),
            **(facts.get("local_macro_features") or {}),
        }
        return _select(FEATURES["news"], news_values)
    if agent == "investor_flow":
        market = facts.get("local_market_features") or {}
        if not all(name in market for name in (
            "return_1d", "return_5d", "sma_20_gap", "volatility_20", "volume_ratio"
        )):
            return None
        values = {
            **(facts.get("local_flow_features") or {}),
            **flow_market_features(market),
        }
        return _select(FEATURES["investor_flow"], values)
    findings = facts.get("agent_findings") or {}
    prediction = facts.get("prediction") or {}
    score = facts.get("score") or {}
    patterns = (facts.get("chart_patterns") or {}).get("patterns") or []
    levels = facts.get("support_resistance") or {}
    flow = facts.get("investor_flow") or {}
    common = {
        "rise_probability": _number(prediction.get("rise_probability")),
        "score_coverage": _number(score.get("coverage_ratio")),
        "warning_count": float(len(facts.get("warnings") or [])),
        "pattern_count": float(len(patterns)),
        "range_width": _range_width(levels.get("support"), levels.get("resistance")),
    }
    values = {
        **common,
        "technical_score": _finding_score(findings, "technical"),
        "financial_score": _finding_score(findings, "financial"),
        "news_score": _finding_score(findings, "news"),
        "disclosure_score": _finding_score(findings, "disclosure"),
        "net_quantity": _number(flow.get("foreign_institution_net_quantity")),
    }
    selected = {name: values.get(name) for name in FEATURES[agent]}
    if any(value is None for value in selected.values()):
        return None
    return {name: float(value) for name, value in selected.items()}


def _select(names: tuple[str, ...], values: dict) -> dict[str, float] | None:
    """`_select`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    selected = {name: _number(values.get(name)) for name in names}
    if any(value is None for value in selected.values()):
        return None
    return {name: float(value) for name, value in selected.items()}


def _finding_score(findings: dict, name: str) -> float | None:
    """`_finding_score`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    value = (findings.get(name) or {}).get("value") or {}
    return _number(value.get("score")) if isinstance(value, dict) else None


def _range_width(support: Any, resistance: Any) -> float | None:
    """`_range_width`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    low, high = _number(support), _number(resistance)
    if low is None or high is None or low <= 0 or high < low:
        return None
    return (high - low) / max((high + low) / 2, 1e-9)


def _number(value: Any) -> float | None:
    """`_number`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) != float("inf") else None
