"""모의투자 계좌에 공통으로 적용하는 중앙 위험관리 규칙이다."""

from dataclasses import dataclass
from decimal import Decimal

from app.paper_trading.contracts import (
    PaperAccount,
    PaperFill,
    PaperPosition,
    PaperRiskLimitError,
)

ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class PaperRiskPolicy:
    """과도한 단일 주문, 종목 집중, 현금 소진을 막는 모의투자 한도다."""

    max_order_ratio: Decimal = Decimal("0.30")
    max_position_ratio: Decimal = Decimal("0.40")
    max_invested_ratio: Decimal = Decimal("0.95")
    concentration_warning_ratio: Decimal = Decimal("0.30")
    low_cash_warning_ratio: Decimal = Decimal("0.10")


DEFAULT_PAPER_RISK_POLICY = PaperRiskPolicy()


def validate_buy_risk(
    account: PaperAccount,
    positions: list[PaperPosition],
    fill: PaperFill,
    *,
    policy: PaperRiskPolicy = DEFAULT_PAPER_RISK_POLICY,
) -> None:
    """매수 체결 후 비중을 미리 계산해 중앙 위험한도를 초과하면 거절한다."""
    if fill.side != "buy":
        return

    cash = account.cash_usd if fill.currency == "USD" else account.cash_krw
    current_values = _position_values(positions, fill.currency)
    current_market_value = sum(current_values.values(), ZERO)
    current_equity = cash + current_market_value
    if current_equity <= ZERO:
        raise PaperRiskLimitError("모의 계좌 자산이 없어 매수할 수 없습니다.")

    notional = fill.fill_price * fill.quantity
    commission = notional * fill.commission_rate
    projected_equity = current_equity - commission
    projected_cash = cash - notional - commission
    projected_values = dict(current_values)
    projected_values[fill.symbol] = projected_values.get(fill.symbol, ZERO) + notional
    projected_market_value = sum(projected_values.values(), ZERO)

    order_ratio = notional / current_equity
    position_ratio = projected_values[fill.symbol] / projected_equity
    invested_ratio = projected_market_value / projected_equity
    if order_ratio > policy.max_order_ratio:
        raise PaperRiskLimitError(
            f"한 번의 매수는 총자산의 {policy.max_order_ratio * 100:.0f}%까지 가능합니다."
        )
    if position_ratio > policy.max_position_ratio:
        raise PaperRiskLimitError(
            f"한 종목은 총자산의 {policy.max_position_ratio * 100:.0f}%까지 보유할 수 있습니다."
        )
    if projected_cash < ZERO or invested_ratio > policy.max_invested_ratio:
        raise PaperRiskLimitError(
            f"현금을 최소 {(ONE - policy.max_invested_ratio) * 100:.0f}% 남겨야 합니다."
        )


def summarize_portfolio_risk(
    account: PaperAccount,
    positions: list[PaperPosition],
    currency: str,
    *,
    policy: PaperRiskPolicy = DEFAULT_PAPER_RISK_POLICY,
) -> dict:
    """화면과 API가 함께 사용할 통화별 위험상태와 경고를 계산한다."""
    cash = account.cash_usd if currency == "USD" else account.cash_krw
    values = _position_values(positions, currency)
    market_value = sum(values.values(), ZERO)
    equity = cash + market_value
    invested_ratio = market_value / equity if equity > ZERO else ZERO
    cash_ratio = cash / equity if equity > ZERO else ZERO
    largest_symbol, largest_value = max(
        values.items(), key=lambda item: item[1], default=(None, ZERO)
    )
    largest_position_ratio = largest_value / equity if equity > ZERO else ZERO

    warnings: list[str] = []
    if largest_position_ratio >= policy.concentration_warning_ratio and largest_symbol:
        warnings.append("single_position_concentration")
    if cash_ratio <= policy.low_cash_warning_ratio and market_value > ZERO:
        warnings.append("low_cash_buffer")

    status = "high" if len(warnings) > 1 else "caution" if warnings else "stable"
    return {
        "status": status,
        "invested_ratio": invested_ratio,
        "cash_ratio": cash_ratio,
        "largest_position_symbol": largest_symbol,
        "largest_position_ratio": largest_position_ratio,
        "warnings": warnings,
        "limits": {
            "max_order_ratio": policy.max_order_ratio,
            "max_position_ratio": policy.max_position_ratio,
            "max_invested_ratio": policy.max_invested_ratio,
        },
    }


def _position_values(positions: list[PaperPosition], currency: str) -> dict[str, Decimal]:
    """최근 저장 가격을 기준으로 해당 통화 포지션의 평가금액을 반환한다."""
    return {
        position.symbol: position.last_price * position.quantity
        for position in positions
        if position.currency == currency and position.quantity > ZERO
    }
