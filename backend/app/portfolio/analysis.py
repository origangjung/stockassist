from decimal import Decimal

from app.providers.contracts import Holding, HoldingsSnapshot

ANALYSIS_VERSION = "portfolio-2026.2"


def analyze_portfolio(snapshot: HoldingsSnapshot) -> dict:
    by_currency: dict[str, list[Holding]] = {}
    for holding in snapshot.holdings:
        by_currency.setdefault(holding.currency, []).append(holding)

    currencies = {
        currency: _currency_analysis(holdings) for currency, holdings in sorted(by_currency.items())
    }
    if any(item["loss_exposure"] >= Decimal("0.25") for item in currencies.values()):
        reference_signal = "loss_watch"
    elif any(item["concentration_level"] == "high" for item in currencies.values()):
        reference_signal = "concentration_watch"
    else:
        reference_signal = "balanced_monitor"

    return {
        "analysis_version": ANALYSIS_VERSION,
        "currency_separated": True,
        "currencies": currencies,
        "reference_signal": reference_signal,
        "experimental": True,
        "is_investment_advice": False,
        "execution_enabled": False,
    }


def _currency_analysis(holdings: list[Holding]) -> dict:
    market_value = sum((item.market_value for item in holdings), Decimal("0"))
    purchase_amount = sum((item.purchase_amount for item in holdings), Decimal("0"))
    profit_after_cost = sum((item.profit_loss_after_cost for item in holdings), Decimal("0"))
    allocations = [
        item.market_value / market_value if market_value else Decimal("0") for item in holdings
    ]
    hhi = sum((allocation * allocation for allocation in allocations), Decimal("0"))
    largest_index = max(range(len(holdings)), key=lambda index: allocations[index])
    loss_value = sum(
        (item.market_value for item in holdings if item.profit_loss_after_cost < 0),
        Decimal("0"),
    )
    largest_allocation = allocations[largest_index]
    concentration_level = (
        "high"
        if largest_allocation >= Decimal("0.5") or hhi >= Decimal("0.35")
        else "moderate"
        if largest_allocation >= Decimal("0.3") or hhi >= Decimal("0.2")
        else "balanced"
    )
    risk_flags: list[str] = []
    if concentration_level == "high":
        risk_flags.append("high_concentration")
    loss_exposure = loss_value / market_value if market_value else Decimal("0")
    if loss_exposure >= Decimal("0.25"):
        risk_flags.append("loss_concentration")
    if profit_after_cost < 0:
        risk_flags.append("negative_after_cost_return")

    return {
        "holding_count": len(holdings),
        "market_value": market_value,
        "purchase_amount": purchase_amount,
        "profit_loss_after_cost": profit_after_cost,
        "profit_rate_after_cost": (
            profit_after_cost / purchase_amount if purchase_amount else Decimal("0")
        ),
        "profitable_count": sum(item.profit_loss_after_cost >= 0 for item in holdings),
        "loss_making_count": sum(item.profit_loss_after_cost < 0 for item in holdings),
        "largest_symbol": holdings[largest_index].symbol,
        "largest_allocation": largest_allocation,
        "concentration_index": hhi,
        "effective_holding_count": Decimal("1") / hhi if hhi else Decimal("0"),
        "concentration_level": concentration_level,
        "loss_exposure": loss_exposure,
        "risk_flags": risk_flags,
    }
