"""시장 데이터, 모의 계좌, 최적화기를 조합해 리밸런싱 제안을 만든다."""

from decimal import Decimal, ROUND_DOWN

import pandas as pd

from app.fund_management.contracts import (
    AllocationMandate,
    FundManagementError,
    PortfolioOptimizer,
)
from app.paper_trading.risk import DEFAULT_PAPER_RISK_POLICY
from app.services.market import MarketDataService
from app.services.paper_trading import PaperTradingService

ZERO = Decimal("0")
QUANTITY_UNIT = Decimal("0.000001")
MIN_REBALANCE_RATIO = Decimal("0.005")


class FundManagementService:
    """실제 주문 권한 없이 목표 비중과 모의 리밸런싱 목록만 산출한다."""

    def __init__(
        self,
        market: MarketDataService,
        paper_trading: PaperTradingService,
        optimizer: PortfolioOptimizer,
    ) -> None:
        """시세, 모의 원장, 최적화 구현체를 주입받는다."""
        self._market = market
        self._paper_trading = paper_trading
        self._optimizer = optimizer

    def propose(
        self,
        account_id: str,
        *,
        symbols: list[str],
        objective: str,
        invest_ratio: Decimal,
        min_asset_weight: Decimal,
        max_asset_weight: Decimal,
        lookback_days: int,
    ) -> dict:
        """과거 가격과 현재 모의 보유량을 비교해 실행되지 않는 주문 제안을 반환한다."""
        universe = list(dict.fromkeys(symbol.strip().upper() for symbol in symbols))
        mandate = AllocationMandate(
            objective=objective,
            invest_ratio=invest_ratio,
            min_asset_weight=min_asset_weight,
            max_asset_weight=max_asset_weight,
            lookback_days=lookback_days,
        )
        self._validate_mandate(universe, mandate)

        prices: dict[str, pd.Series] = {}
        metadata: dict[str, dict] = {}
        currencies: set[str] = set()
        price_basis_warnings: list[str] = []
        for symbol in universe:
            stock, provider = self._market.stock_info(symbol)
            candles, _ = self._market.candles(symbol, lookback_days)
            if len(candles) < 60:
                raise FundManagementError(f"{symbol}의 가격 관측치가 60개보다 적습니다.")
            currencies.add(stock.currency.upper())
            metadata[symbol] = {
                "name": stock.name,
                "market": stock.market,
                "currency": stock.currency.upper(),
                "provider": provider,
                "last_price": candles[-1].close,
            }
            prices[symbol] = pd.Series(
                [float(candle.close) for candle in candles],
                index=[candle.timestamp for candle in candles],
                name=symbol,
            )
            if any(candle.price_basis in {"unknown", "unadjusted"} for candle in candles):
                price_basis_warnings.append(symbol)

        if len(currencies) != 1:
            raise FundManagementError("한 제안에서는 같은 통화의 종목만 선택할 수 있습니다.")
        currency = currencies.pop()
        price_frame = pd.concat(prices.values(), axis=1, join="inner").dropna()
        risky_weights = self._optimizer.optimize(price_frame, mandate)
        target_weights = {
            symbol: (risky_weights.get(symbol, ZERO) * invest_ratio)
            for symbol in universe
        }

        snapshot = self._paper_trading.snapshot(account_id)
        totals = snapshot["totals"][currency]
        equity = Decimal(str(totals["equity"]))
        current_positions = {
            row["symbol"]: row
            for row in snapshot["positions"]
            if row["currency"] == currency
        }
        actions = self._rebalance_actions(
            universe, target_weights, metadata, current_positions, equity
        )
        current_weights = {
            symbol: Decimal(str(row["market_value"])) / equity if equity > ZERO else ZERO
            for symbol, row in current_positions.items()
        }
        warnings = ["제안 결과이며 실제 주문은 실행되지 않습니다."]
        if price_basis_warnings:
            warnings.append(
                "수정주가 검증이 끝나지 않은 종목: " + ", ".join(sorted(price_basis_warnings))
            )

        return {
            "account_id": account_id,
            "currency": currency,
            "objective": objective,
            "optimizer": self._optimizer.name,
            "lookback_days": lookback_days,
            "observation_count": len(price_frame),
            "equity": equity,
            "target_weights": target_weights,
            "target_cash_weight": Decimal("1") - invest_ratio,
            "current_weights": current_weights,
            "rebalance_actions": actions,
            "estimated_turnover": sum(
                (Decimal(str(action["notional"])) for action in actions), ZERO
            ) / equity if equity > ZERO else ZERO,
            "warnings": warnings,
            "execution_enabled": False,
            "is_real_order": False,
            "is_investment_advice": False,
        }

    @staticmethod
    def _validate_mandate(universe: list[str], mandate: AllocationMandate) -> None:
        """요청값이 중앙 위험정책과 수학적으로 가능한 범위인지 확인한다."""
        if len(universe) < 2:
            raise FundManagementError("자금배분에는 서로 다른 종목이 최소 2개 필요합니다.")
        if len(universe) > 12:
            raise FundManagementError("한 번에 최대 12개 종목까지 분석할 수 있습니다.")
        if mandate.invest_ratio > DEFAULT_PAPER_RISK_POLICY.max_invested_ratio:
            raise FundManagementError("투자 비중은 중앙 위험정책의 95% 한도를 넘을 수 없습니다.")
        if mandate.max_asset_weight > DEFAULT_PAPER_RISK_POLICY.max_position_ratio:
            raise FundManagementError("종목당 목표 비중은 중앙 위험정책의 40% 한도를 넘을 수 없습니다.")
        if mandate.min_asset_weight > mandate.max_asset_weight:
            raise FundManagementError("최소 종목 비중은 최대 종목 비중보다 클 수 없습니다.")
        count = Decimal(len(universe))
        if mandate.min_asset_weight * count > Decimal("1"):
            raise FundManagementError("최소 비중과 종목 수의 조합으로는 포트폴리오를 만들 수 없습니다.")
        if mandate.max_asset_weight * count < Decimal("1"):
            raise FundManagementError("최대 비중과 종목 수의 조합으로는 포트폴리오를 만들 수 없습니다.")

    @staticmethod
    def _rebalance_actions(
        universe: list[str],
        target_weights: dict[str, Decimal],
        metadata: dict[str, dict],
        current_positions: dict[str, dict],
        equity: Decimal,
    ) -> list[dict]:
        """현재 평가금액과 목표 평가금액의 차이를 모의 주문 후보로 변환한다."""
        actions: list[dict] = []
        all_symbols = list(dict.fromkeys([*universe, *current_positions]))
        for symbol in all_symbols:
            target_weight = target_weights.get(symbol, ZERO)
            current_value = Decimal(str(current_positions.get(symbol, {}).get("market_value", ZERO)))
            target_value = equity * target_weight
            delta = target_value - current_value
            if equity <= ZERO or abs(delta) / equity < MIN_REBALANCE_RATIO:
                continue
            action_notional = abs(delta)
            staged = False
            if delta > ZERO:
                max_buy_notional = equity * DEFAULT_PAPER_RISK_POLICY.max_order_ratio
                if action_notional > max_buy_notional:
                    action_notional = max_buy_notional
                    staged = True
            last_price = Decimal(str(
                metadata.get(symbol, {}).get(
                    "last_price", current_positions.get(symbol, {}).get("last_price", ZERO)
                )
            ))
            if last_price <= ZERO:
                continue
            actions.append({
                "symbol": symbol,
                "side": "buy" if delta > ZERO else "sell",
                "quantity": (action_notional / last_price).quantize(
                    QUANTITY_UNIT, rounding=ROUND_DOWN
                ),
                "notional": action_notional.quantize(Decimal("0.01")),
                "target_weight": target_weight,
                "reason": (
                    "staged_for_order_limit"
                    if staged
                    else "target_allocation_gap"
                    if symbol in universe
                    else "outside_universe"
                ),
            })
        return actions
