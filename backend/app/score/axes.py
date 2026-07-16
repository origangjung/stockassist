from decimal import Decimal
from math import tanh
from typing import Any

AxisInput = tuple[float | None, list[str]]


def financial_axis(snapshot: dict[str, Any]) -> AxisInput:
    revenue = _number(snapshot.get("revenue"))
    operating_income = _number(snapshot.get("operating_income"))
    net_income = _number(snapshot.get("net_income"))
    assets = _number(snapshot.get("total_assets"))
    equity = _number(snapshot.get("total_equity"))
    components: list[float] = []
    evidence: list[str] = []

    if revenue and operating_income is not None:
        margin = operating_income / revenue
        components.append(_clamp(50 + 30 * tanh(margin / 0.15)))
        evidence.append(f"영업이익률 {margin:.1%}")
    if revenue and net_income is not None:
        margin = net_income / revenue
        components.append(_clamp(50 + 30 * tanh(margin / 0.15)))
        evidence.append(f"순이익률 {margin:.1%}")
    if assets and equity is not None:
        equity_ratio = equity / assets
        components.append(_clamp(50 + (equity_ratio - 0.5) * 60))
        evidence.append(f"자기자본비율 {equity_ratio:.1%}")
    return _average(components, evidence, "계산 가능한 핵심 재무 항목이 없습니다.")


def news_axis(snapshot: dict[str, Any]) -> AxisInput:
    sentiment = _number(snapshot.get("sentiment_score"))
    if sentiment is None:
        return None, ["뉴스 감성 점수가 없습니다."]
    label = str(snapshot.get("sentiment_label", "unknown"))
    score = _clamp(50 + 25 * tanh(sentiment))
    return round(score, 4), [f"뉴스 감성 {label} ({sentiment:.3f})"]


def disclosure_axis(snapshot: dict[str, Any]) -> AxisInput:
    disclosures = snapshot.get("disclosures")
    risk_flags = snapshot.get("risk_flags")
    if not isinstance(disclosures, list) or not isinstance(risk_flags, list):
        return None, ["공시 분석 결과가 없습니다."]
    score = _clamp(50 - min(40, len(risk_flags) * 20))
    evidence = [f"최근 공시 {len(disclosures)}건", f"고위험 공시 {len(risk_flags)}건"]
    return round(score, 4), evidence


def investor_flow_axis(snapshot: dict[str, Any]) -> AxisInput:
    combined = _number(snapshot.get("foreign_institution_net_quantity"))
    if combined is None:
        return None, ["외국인·기관 합산 수급이 없습니다."]
    holding = _number(snapshot.get("foreign_holding_quantity"))
    if holding and holding > 0:
        normalized = combined / holding
        score = _clamp(50 + 30 * tanh(normalized / 0.001))
        evidence = [
            f"외국인·기관 합산 순매수 {combined:,.0f}주",
            f"외국인 보유량 대비 {normalized:.3%}",
        ]
    else:
        score = 60 if combined > 0 else 40 if combined < 0 else 50
        evidence = [f"외국인·기관 합산 순매수 {combined:,.0f}주"]
    return round(score, 4), evidence


def market_risk_axis(warnings: list[Any]) -> AxisInput:
    if not warnings:
        return 50.0, ["활성 종목 투자유의 신호 없음"]
    warning_types = [str(getattr(item, "warning_type", "unknown")) for item in warnings]
    severe_terms = ("risk", "liquidation", "delisting", "투자위험", "정리매매")
    penalty = sum(
        25 if any(term in warning_type.casefold() for term in severe_terms) else 15
        for warning_type in warning_types
    )
    return _clamp(50 - min(40, penalty)), [
        f"활성 투자유의 {len(warning_types)}건",
        *warning_types[:3],
    ]


def unavailable_axis(message: str) -> AxisInput:
    return None, [message]


def _number(value: Any) -> float | None:
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        return float(value)
    return None


def _average(components: list[float], evidence: list[str], missing: str) -> AxisInput:
    if not components:
        return None, [missing]
    return round(sum(components) / len(components), 4), evidence


def _clamp(value: float, lower: float = 0, upper: float = 100) -> float:
    return max(lower, min(upper, value))
