from datetime import datetime, timedelta, timezone
from decimal import Decimal
import random

from app.providers.contracts import (
    BrokerAccount,
    Candle,
    Holding,
    HoldingsSnapshot,
    OrderbookLevel,
    ProviderCapabilities,
    Quote,
    StockInfo,
    StockProvider,
    StockWarning,
    Trade,
)
from app.providers.errors import ProviderNotFoundError


_STOCKS = {
    "005930": ("삼성전자", Decimal("74800"), Decimal("1200"), 14_201_392, "전기전자", "1975-06-11"),
    "000660": (
        "SK하이닉스",
        Decimal("237500"),
        Decimal("6500"),
        3_843_281,
        "전기전자",
        "1996-12-26",
    ),
    "035420": ("NAVER", Decimal("195200"), Decimal("2100"), 1_322_984, "서비스업", "2002-10-29"),
}


_US_STOCKS = {
    "AAPL": ("Apple", Decimal("214.15"), Decimal("1.82"), 54_182_000, "Technology", "1980-12-12"),
    "MSFT": (
        "Microsoft",
        Decimal("510.24"),
        Decimal("3.17"),
        21_406_000,
        "Technology",
        "1986-03-13",
    ),
    "NVDA": (
        "NVIDIA",
        Decimal("177.91"),
        Decimal("4.23"),
        145_224_000,
        "Semiconductors",
        "1999-01-22",
    ),
    "TSLA": ("Tesla", Decimal("313.51"), Decimal("-2.61"), 89_105_000, "Automotive", "2010-06-29"),
    "JPM": (
        "JPMorgan Chase",
        Decimal("289.74"),
        Decimal("0.66"),
        8_314_000,
        "Financial Services",
        "1969-03-05",
    ),
}

_US_MARKETS = {"JPM": "NYSE"}


class UnknownSymbolError(ProviderNotFoundError):
    """Backward-compatible alias for callers of the original mock provider."""


class MockProvider(StockProvider):
    """Deterministic data source for pipeline and API contract development."""

    name = "mock"
    capabilities = ProviderCapabilities(
        supports_quote=True,
        supports_orderbook=True,
        supports_trades=True,
        supports_candles=True,
        supports_streaming=False,
        supports_orders=False,
        supports_conditional_orders=False,
        supports_investor_flow=False,
        supports_account_sync=True,
        supports_warnings=True,
    )

    def _stock(self, symbol: str) -> tuple[str, Decimal, Decimal, int, str, str]:
        try:
            if symbol in _US_STOCKS:
                return _US_STOCKS[symbol]
            return _STOCKS[symbol]
        except KeyError as exc:
            raise UnknownSymbolError(f"지원하지 않는 Mock 종목입니다: {symbol}") from exc

    @staticmethod
    def _market_currency(symbol: str) -> tuple[str, str]:
        if symbol in _US_STOCKS:
            return _US_MARKETS.get(symbol, "NASDAQ"), "USD"
        return ("KOSPI" if symbol != "035420" else "KOSDAQ"), "KRW"

    def get_quote(self, symbol: str) -> Quote:
        name, price, change, volume, _, _ = self._stock(symbol)
        previous_close = price - change
        _, currency = self._market_currency(symbol)
        return Quote(
            symbol,
            name,
            price,
            change,
            (change / previous_close * 100).quantize(Decimal(".01")),
            volume,
            datetime.now(timezone.utc),
            currency,
        )

    def get_candles(self, symbol: str, limit: int = 30) -> list[Candle]:
        _, current, _, _, _, _ = self._stock(symbol)
        _, currency = self._market_currency(symbol)
        rng = random.Random(f"stockpilot:{symbol}")
        base = current * Decimal("0.91")
        start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=limit - 1)
        candles: list[Candle] = []
        for index in range(limit):
            drift = Decimal(str(rng.uniform(-0.022, 0.026)))
            open_price = base
            quantum = Decimal("0.01") if currency == "USD" else Decimal("1")
            close = (base * (Decimal("1") + drift)).quantize(quantum)
            high = max(open_price, close) * Decimal(str(1 + rng.uniform(0.001, 0.014)))
            low = min(open_price, close) * Decimal(str(1 - rng.uniform(0.001, 0.014)))
            candles.append(
                Candle(
                    start + timedelta(days=index),
                    open_price.quantize(quantum),
                    high.quantize(quantum),
                    low.quantize(quantum),
                    close,
                    rng.randint(500_000, 15_000_000),
                )
            )
            base = close
        return candles

    def get_orderbook(self, symbol: str) -> tuple[list[OrderbookLevel], list[OrderbookLevel]]:
        quote = self.get_quote(symbol)
        tick = (
            Decimal("0.01")
            if quote.currency == "USD"
            else (Decimal("100") if quote.price >= Decimal("10000") else Decimal("10"))
        )
        asks = [OrderbookLevel(quote.price + tick * (i + 1), 1000 * (6 - i)) for i in range(5)]
        bids = [OrderbookLevel(quote.price - tick * (i + 1), 1200 * (6 - i)) for i in range(5)]
        return asks, bids

    def get_trades(self, symbol: str, limit: int = 20) -> list[Trade]:
        quote = self.get_quote(symbol)
        rng = random.Random(f"stockpilot:trades:{symbol}")
        now = datetime.now(timezone.utc).replace(microsecond=0)
        tick = (
            Decimal("0.01")
            if quote.currency == "USD"
            else (Decimal("100") if quote.price >= Decimal("10000") else Decimal("10"))
        )
        return [
            Trade(
                symbol=symbol,
                price=quote.price + tick * rng.randint(-4, 4),
                quantity=Decimal(rng.randint(1, 500)),
                side="buy" if rng.random() > 0.45 else "sell",
                executed_at=now - timedelta(seconds=index * rng.randint(2, 12)),
            )
            for index in range(limit)
        ]

    def get_stock_info(self, symbol: str) -> StockInfo:
        name, _, _, _, sector, listed_at = self._stock(symbol)
        market, currency = self._market_currency(symbol)
        return StockInfo(
            symbol=symbol,
            name=name,
            market=market,
            sector=sector,
            listed_at=datetime.fromisoformat(f"{listed_at}T00:00:00+00:00"),
            currency=currency,
        )

    def get_warnings(self, symbol: str) -> list[StockWarning]:
        self._stock(symbol)
        return []

    def get_accounts(self) -> list[BrokerAccount]:
        return [BrokerAccount(account_seq=1, account_no="12345678901", account_type="BROKERAGE")]

    def get_holdings(self, account_seq: int) -> HoldingsSnapshot:
        if account_seq != 1:
            raise ProviderNotFoundError("Mock account was not found", code="account-not-found")
        samsung = self.get_quote("005930")
        apple = self.get_quote("AAPL")
        holdings = [
            _mock_holding(samsung, Decimal("20"), Decimal("68000"), "KR"),
            _mock_holding(apple, Decimal("5"), Decimal("190"), "US"),
        ]
        return _snapshot(account_seq, holdings)


def _mock_holding(
    quote: Quote, quantity: Decimal, average_price: Decimal, market_country: str
) -> Holding:
    purchase_amount = quantity * average_price
    market_value = quantity * quote.price
    profit_loss = market_value - purchase_amount
    profit_rate = profit_loss / purchase_amount if purchase_amount else Decimal("0")
    daily_profit_loss = quantity * (quote.change or Decimal("0"))
    previous_value = market_value - daily_profit_loss
    daily_rate = daily_profit_loss / previous_value if previous_value else Decimal("0")
    return Holding(
        symbol=quote.symbol,
        name=quote.name or quote.symbol,
        market_country=market_country,
        currency=quote.currency or "KRW",
        quantity=quantity,
        last_price=quote.price,
        average_purchase_price=average_price,
        purchase_amount=purchase_amount,
        market_value=market_value,
        market_value_after_cost=market_value,
        profit_loss=profit_loss,
        profit_loss_after_cost=profit_loss,
        profit_rate=profit_rate,
        profit_rate_after_cost=profit_rate,
        daily_profit_loss=daily_profit_loss,
        daily_profit_rate=daily_rate,
        commission=None,
        tax=None,
    )


def _snapshot(account_seq: int, holdings: list[Holding]) -> HoldingsSnapshot:
    currencies = {"KRW", "USD"}

    def totals(attribute: str) -> dict[str, Decimal | None]:
        values = {
            currency: sum(
                (getattr(item, attribute) for item in holdings if item.currency == currency),
                Decimal("0"),
            )
            for currency in currencies
        }
        return {
            currency: value if any(item.currency == currency for item in holdings) else None
            for currency, value in values.items()
        }

    total_purchase = totals("purchase_amount")
    value = totals("market_value")
    value_after_cost = totals("market_value_after_cost")
    profit = totals("profit_loss")
    profit_after_cost = totals("profit_loss_after_cost")
    daily = totals("daily_profit_loss")
    combined_purchase = sum((item.purchase_amount for item in holdings), Decimal("0"))
    combined_profit = sum((item.profit_loss for item in holdings), Decimal("0"))
    combined_after_cost = sum((item.profit_loss_after_cost for item in holdings), Decimal("0"))
    combined_value = sum((item.market_value for item in holdings), Decimal("0"))
    combined_daily = sum((item.daily_profit_loss for item in holdings), Decimal("0"))
    return HoldingsSnapshot(
        account_seq=account_seq,
        total_purchase_amount=total_purchase,
        market_value=value,
        market_value_after_cost=value_after_cost,
        profit_loss=profit,
        profit_loss_after_cost=profit_after_cost,
        profit_rate=combined_profit / combined_purchase if combined_purchase else Decimal("0"),
        profit_rate_after_cost=combined_after_cost / combined_purchase
        if combined_purchase
        else Decimal("0"),
        daily_profit_loss=daily,
        daily_profit_rate=combined_daily / (combined_value - combined_daily)
        if combined_value != combined_daily
        else Decimal("0"),
        holdings=holdings,
        fetched_at=datetime.now(timezone.utc),
    )
