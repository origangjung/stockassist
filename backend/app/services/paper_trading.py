"""실제 주문 기능과 분리된 모의 시장가 체결 및 평가 서비스다."""

from dataclasses import asdict, replace
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from app.paper_trading.contracts import PaperFill
from app.paper_trading.risk import summarize_portfolio_risk
from app.repositories.paper_trading import PaperTradingRepository
from app.services.market import MarketDataService

COMMISSION_RATE = Decimal("0.001")
MONEY_UNIT = Decimal("0.01")


class PaperTradingService:
    """검증된 현재가로만 모의 체결하고 통화별 자산을 계산한다."""

    def __init__(self, market: MarketDataService, repository: PaperTradingRepository):
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._market = market
        self._repository = repository

    def snapshot(self, account_id: str) -> dict:
        """보유 종목을 최신 시세로 평가하되 시세 장애 시 마지막 체결가를 사용한다."""
        return self._serialize(self._repository.snapshot(account_id))

    def execute(
        self,
        account_id: str,
        *,
        symbol: str,
        side: str,
        quantity: Decimal,
        idempotency_key: str,
    ) -> dict:
        """공급자 종목 메타데이터와 현재가를 조회한 뒤 모의 원장에 한 번만 반영한다."""
        quote, _ = self._market.quote(symbol)
        stock, _ = self._market.stock_info(symbol)
        currency = (quote.currency or stock.currency or "KRW").upper()
        if currency not in {"KRW", "USD"}:
            raise ValueError("모의투자는 현재 KRW와 USD 종목만 지원합니다.")
        fill = PaperFill(
            idempotency_key=idempotency_key,
            symbol=stock.symbol,
            name=quote.name or stock.name,
            market=stock.market,
            currency=currency,
            side=side,
            quantity=quantity,
            fill_price=quote.price,
            commission_rate=COMMISSION_RATE,
            executed_at=quote.as_of or datetime.now(timezone.utc),
        )
        return self._serialize(self._repository.execute(account_id, fill))

    def reset(self, account_id: str) -> dict:
        """해당 모의 계좌의 보유 종목과 주문 원장만 초기 상태로 되돌린다."""
        return self._serialize(self._repository.reset(account_id))

    def _serialize(self, state) -> dict:
        """`_serialize`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        account, positions, orders = state
        totals = {
            "KRW": {
                "initial_cash": account.initial_cash_krw,
                "cash": account.cash_krw,
                "market_value": Decimal("0"),
                "unrealized_pnl": Decimal("0"),
            },
            "USD": {
                "initial_cash": account.initial_cash_usd,
                "cash": account.cash_usd,
                "market_value": Decimal("0"),
                "unrealized_pnl": Decimal("0"),
            },
        }
        serialized_positions = []
        repriced_positions = []
        for position in positions:
            last_price = position.last_price
            price_as_of = position.updated_at
            price_status = "last_fill"
            try:
                quote, _ = self._market.quote(position.symbol)
                last_price = quote.price
                price_as_of = quote.as_of or datetime.now(timezone.utc)
                price_status = "live"
            except Exception:  # 공급자 장애가 계좌 원장 조회까지 막지 않도록 마지막 체결가로 평가한다.
                pass
            market_value = (last_price * position.quantity).quantize(MONEY_UNIT, ROUND_HALF_UP)
            unrealized = ((last_price - position.average_price) * position.quantity).quantize(MONEY_UNIT, ROUND_HALF_UP)
            bucket = totals[position.currency]
            bucket["market_value"] += market_value
            bucket["unrealized_pnl"] += unrealized
            repriced_positions.append(replace(position, last_price=last_price))
            serialized_positions.append({
                **asdict(position),
                "last_price": last_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized,
                "return_percent": (
                    ((last_price / position.average_price) - 1) * 100
                ).quantize(Decimal("0.01"), ROUND_HALF_UP),
                "price_as_of": price_as_of,
                "price_status": price_status,
            })
        for bucket in totals.values():
            bucket["equity"] = (bucket["cash"] + bucket["market_value"]).quantize(MONEY_UNIT)
            bucket["total_pnl"] = (bucket["equity"] - bucket["initial_cash"]).quantize(MONEY_UNIT)
            return_percent = (
                (bucket["total_pnl"] / bucket["initial_cash"]) * 100
            ).quantize(Decimal("0.01"), ROUND_HALF_UP)
            bucket["return_percent"] = Decimal("0.00") if return_percent == 0 else return_percent
        return {
            "account": asdict(account),
            "persistence_status": self._repository.persistence_status,
            "saved_at": account.updated_at,
            "totals": totals,
            "risk": {
                currency: summarize_portfolio_risk(account, repriced_positions, currency)
                for currency in ("KRW", "USD")
            },
            "positions": serialized_positions,
            "orders": [asdict(order) for order in orders],
            "commission_rate": COMMISSION_RATE,
            "execution_policy": "현재 조회가로 즉시 체결되는 모의 시장가 주문",
            "is_real_order": False,
        }
