from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx2

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
from app.providers.errors import ProviderNotFoundError, ProviderUnavailableError
from app.providers.audit import ProviderAuditSink
from app.providers.toss.auth import InMemoryTokenCache, TokenCache, TossTokenManager
from app.providers.toss.client import TossApiClient
from app.providers.toss.rate_limit import TossRateLimiter


class TossProvider(StockProvider):
    name = "toss"
    capabilities = ProviderCapabilities(
        supports_quote=True,
        supports_orderbook=True,
        supports_trades=True,
        supports_candles=True,
        supports_streaming=False,
        # Order execution remains deliberately disabled until Phase 17's regulatory gate.
        supports_orders=False,
        supports_conditional_orders=False,
        supports_investor_flow=False,
        supports_account_sync=True,
        supports_warnings=True,
    )

    def __init__(self, api: TossApiClient) -> None:
        self._api = api
        self._stock_cache: dict[str, StockInfo] = {}

    @classmethod
    def create(
        cls,
        *,
        base_url: str,
        client_id: str,
        client_secret: str,
        timeout_seconds: float = 10,
        max_retries: int = 3,
        token_cache: TokenCache | None = None,
        transport: httpx2.BaseTransport | None = None,
        audit_sink: ProviderAuditSink | None = None,
    ) -> "TossProvider":
        http = httpx2.Client(
            base_url=base_url,
            timeout=timeout_seconds,
            transport=transport,
            headers={"Accept": "application/json"},
        )
        limiter = TossRateLimiter()
        tokens = TossTokenManager(
            http,
            limiter,
            client_id=client_id,
            client_secret=client_secret,
            cache=token_cache or InMemoryTokenCache(),
        )
        return cls(
            TossApiClient(
                http,
                tokens,
                limiter,
                max_retries=max_retries,
                audit_sink=audit_sink,
            )
        )

    def get_quote(self, symbol: str) -> Quote:
        payload = self._api.get("/api/v1/prices", group="MARKET_DATA", params={"symbols": symbol})
        rows = _result_list(payload)
        row = _find_symbol(rows, symbol)
        stock = self._stock_cache.get(symbol)
        if stock is None:
            stock = self.get_stock_info(symbol)
        return Quote(
            symbol=symbol,
            name=stock.name,
            price=_decimal(row, "lastPrice"),
            change=None,
            change_percent=None,
            volume=None,
            as_of=_optional_datetime(row.get("timestamp")),
            currency=_optional_string(row.get("currency")) or stock.currency,
        )

    def get_candles(self, symbol: str, limit: int = 30) -> list[Candle]:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        before: str | None = None
        candles: list[Candle] = []
        while len(candles) < limit:
            count = min(200, limit - len(candles))
            params: dict[str, Any] = {
                "symbol": symbol,
                "interval": "1d",
                "count": count,
                "adjusted": True,
            }
            if before is not None:
                params["before"] = before
            payload = self._api.get("/api/v1/candles", group="MARKET_DATA_CHART", params=params)
            result = _result_object(payload)
            page = result.get("candles")
            if not isinstance(page, list):
                raise ProviderUnavailableError(
                    "Toss candle response omitted the candles array",
                    code="invalid-provider-response",
                )
            candles.extend(_candle(item) for item in page if isinstance(item, dict))
            next_before = result.get("nextBefore")
            if not page or not isinstance(next_before, str) or next_before == before:
                break
            before = next_before
        return sorted(candles, key=lambda item: item.timestamp)[-limit:]

    def get_orderbook(self, symbol: str) -> tuple[list[OrderbookLevel], list[OrderbookLevel]]:
        payload = self._api.get("/api/v1/orderbook", group="MARKET_DATA", params={"symbol": symbol})
        result = _result_object(payload)
        return _levels(result, "asks"), _levels(result, "bids")

    def get_trades(self, symbol: str, limit: int = 20) -> list[Trade]:
        if not 1 <= limit <= 50:
            raise ValueError("Toss trades limit must be between 1 and 50")
        payload = self._api.get(
            "/api/v1/trades",
            group="MARKET_DATA",
            params={"symbol": symbol, "count": limit},
        )
        return [
            Trade(
                symbol=symbol,
                price=_decimal(row, "price"),
                quantity=_decimal(row, "volume"),
                side=None,
                executed_at=_required_datetime(row.get("timestamp")),
            )
            for row in _result_list(payload)
        ]

    def get_stock_info(self, symbol: str) -> StockInfo:
        cached = self._stock_cache.get(symbol)
        if cached is not None:
            return cached
        payload = self._api.get("/api/v1/stocks", group="STOCK", params={"symbols": symbol})
        row = _find_symbol(_result_list(payload), symbol)
        listed_at = _optional_date(row.get("listDate"))
        stock = StockInfo(
            symbol=symbol,
            name=str(row["name"]),
            market=str(row["market"]),
            sector=None,
            listed_at=(
                datetime.combine(listed_at, datetime.min.time(), tzinfo=timezone.utc)
                if listed_at
                else None
            ),
            currency=_optional_string(row.get("currency")) or "KRW",
        )
        self._stock_cache[symbol] = stock
        return stock

    def get_warnings(self, symbol: str) -> list[StockWarning]:
        payload = self._api.get(f"/api/v1/stocks/{symbol}/warnings", group="STOCK")
        return [
            StockWarning(
                warning_type=str(row["warningType"]),
                exchange=_optional_string(row.get("exchange")),
                start_date=_optional_date(row.get("startDate")),
                end_date=_optional_date(row.get("endDate")),
            )
            for row in _result_list(payload)
        ]

    def get_accounts(self) -> list[BrokerAccount]:
        payload = self._api.get("/api/v1/accounts", group="ACCOUNT")
        return [_broker_account(row) for row in _result_list(payload)]

    def get_holdings(self, account_seq: int) -> HoldingsSnapshot:
        payload = self._api.get("/api/v1/holdings", group="ASSET", account_seq=account_seq)
        result = _result_object(payload)
        return _holdings_snapshot(result, account_seq)

    def close(self) -> None:
        self._api.close()


def _result_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    result = payload.get("result")
    if not isinstance(result, list) or not all(isinstance(item, dict) for item in result):
        raise ProviderUnavailableError(
            "Toss returned an invalid result array", code="invalid-provider-response"
        )
    return result


def _result_object(payload: dict[str, Any]) -> dict[str, Any]:
    result = payload.get("result")
    if not isinstance(result, dict):
        raise ProviderUnavailableError(
            "Toss returned an invalid result object", code="invalid-provider-response"
        )
    return result


def _find_symbol(rows: list[dict[str, Any]], symbol: str) -> dict[str, Any]:
    for row in rows:
        if row.get("symbol") == symbol:
            return row
    raise ProviderNotFoundError(f"Toss did not return stock {symbol}", code="stock-not-found")


def _candle(row: dict[str, Any]) -> Candle:
    return Candle(
        timestamp=_required_datetime(row.get("timestamp")),
        open=_decimal(row, "openPrice"),
        high=_decimal(row, "highPrice"),
        low=_decimal(row, "lowPrice"),
        close=_decimal(row, "closePrice"),
        volume=_integer_decimal(row, "volume"),
    )


def _levels(result: dict[str, Any], key: str) -> list[OrderbookLevel]:
    rows = result.get(key)
    if not isinstance(rows, list):
        raise ProviderUnavailableError(
            f"Toss orderbook response omitted {key}", code="invalid-provider-response"
        )
    return [
        OrderbookLevel(
            price=_decimal(row, "price"),
            quantity=_decimal(row, "volume"),
        )
        for row in rows
        if isinstance(row, dict)
    ]


def _decimal(row: dict[str, Any], key: str) -> Decimal:
    try:
        return Decimal(str(row[key]))
    except (KeyError, InvalidOperation, TypeError) as exc:
        raise ProviderUnavailableError(
            f"Toss returned an invalid decimal field: {key}",
            code="invalid-provider-response",
        ) from exc


def _integer_decimal(row: dict[str, Any], key: str) -> int:
    value = _decimal(row, key)
    if value != value.to_integral_value():
        raise ProviderUnavailableError(
            f"Toss returned a fractional {key} unsupported by the KRX domain",
            code="unsupported-fractional-volume",
        )
    return int(value)


def _required_datetime(value: Any) -> datetime:
    parsed = _optional_datetime(value)
    if parsed is None:
        raise ProviderUnavailableError(
            "Toss response omitted a required timestamp", code="invalid-provider-response"
        )
    return parsed


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProviderUnavailableError(
            "Toss returned an invalid timestamp", code="invalid-provider-response"
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _optional_date(value: Any) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ProviderUnavailableError(
            "Toss returned an invalid date", code="invalid-provider-response"
        ) from exc


def _optional_string(value: Any) -> str | None:
    return None if value is None else str(value)


def _broker_account(row: dict[str, Any]) -> BrokerAccount:
    try:
        return BrokerAccount(
            account_seq=int(row["accountSeq"]),
            account_no=str(row["accountNo"]),
            account_type=str(row["accountType"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ProviderUnavailableError(
            "Toss returned an invalid account response", code="invalid-provider-response"
        ) from exc


def _holdings_snapshot(result: dict[str, Any], account_seq: int) -> HoldingsSnapshot:
    items = result.get("items")
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise ProviderUnavailableError(
            "Toss holdings response omitted the items array", code="invalid-provider-response"
        )
    market_value = _required_object(result, "marketValue")
    profit_loss = _required_object(result, "profitLoss")
    daily_profit_loss = _required_object(result, "dailyProfitLoss")
    return HoldingsSnapshot(
        account_seq=account_seq,
        total_purchase_amount=_currency_totals(_required_object(result, "totalPurchaseAmount")),
        market_value=_currency_totals(_required_object(market_value, "amount")),
        market_value_after_cost=_currency_totals(_required_object(market_value, "amountAfterCost")),
        profit_loss=_currency_totals(_required_object(profit_loss, "amount")),
        profit_loss_after_cost=_currency_totals(_required_object(profit_loss, "amountAfterCost")),
        profit_rate=_decimal(profit_loss, "rate"),
        profit_rate_after_cost=_decimal(profit_loss, "rateAfterCost"),
        daily_profit_loss=_currency_totals(_required_object(daily_profit_loss, "amount")),
        daily_profit_rate=_decimal(daily_profit_loss, "rate"),
        holdings=[_holding(item) for item in items],
        fetched_at=datetime.now(timezone.utc),
    )


def _holding(row: dict[str, Any]) -> Holding:
    market_value = _required_object(row, "marketValue")
    profit_loss = _required_object(row, "profitLoss")
    daily_profit_loss = _required_object(row, "dailyProfitLoss")
    cost = _required_object(row, "cost")
    try:
        return Holding(
            symbol=str(row["symbol"]),
            name=str(row["name"]),
            market_country=str(row["marketCountry"]),
            currency=str(row["currency"]),
            quantity=_decimal(row, "quantity"),
            last_price=_decimal(row, "lastPrice"),
            average_purchase_price=_decimal(row, "averagePurchasePrice"),
            purchase_amount=_decimal(market_value, "purchaseAmount"),
            market_value=_decimal(market_value, "amount"),
            market_value_after_cost=_decimal(market_value, "amountAfterCost"),
            profit_loss=_decimal(profit_loss, "amount"),
            profit_loss_after_cost=_decimal(profit_loss, "amountAfterCost"),
            profit_rate=_decimal(profit_loss, "rate"),
            profit_rate_after_cost=_decimal(profit_loss, "rateAfterCost"),
            daily_profit_loss=_decimal(daily_profit_loss, "amount"),
            daily_profit_rate=_decimal(daily_profit_loss, "rate"),
            commission=_optional_decimal(cost, "commission"),
            tax=_optional_decimal(cost, "tax"),
        )
    except KeyError as exc:
        raise ProviderUnavailableError(
            "Toss returned an invalid holding response", code="invalid-provider-response"
        ) from exc


def _required_object(row: dict[str, Any], key: str) -> dict[str, Any]:
    value = row.get(key)
    if not isinstance(value, dict):
        raise ProviderUnavailableError(
            f"Toss returned an invalid object field: {key}",
            code="invalid-provider-response",
        )
    return value


def _currency_totals(row: dict[str, Any]) -> dict[str, Decimal | None]:
    return {"KRW": _optional_decimal(row, "krw"), "USD": _optional_decimal(row, "usd")}


def _optional_decimal(row: dict[str, Any], key: str) -> Decimal | None:
    if row.get(key) is None:
        return None
    return _decimal(row, key)
