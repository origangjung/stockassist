"""provider 파일은 외부 데이터 공급자 연동 기능을 담당한다."""

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx2

from app.providers.contracts import (
    BrokerAccount,
    Candle,
    CandlePriceBasisPolicy,
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
    """외부 또는 모의 데이터 원천을 동일한 계약으로 제공하는 구현체입니다."""

    name = "toss"
    candle_price_basis_policy = CandlePriceBasisPolicy(
        expected_basis="provider_adjusted",
        verification_status="verified",
        rule_version="toss-adjusted-v1",
        evidence="Daily candle request fixes adjusted=true",
    )
    capabilities = ProviderCapabilities(
        supports_quote=True,
        supports_orderbook=True,
        supports_trades=True,
        supports_candles=True,
        supports_streaming=True,
        # Order execution remains deliberately disabled until Phase 17's regulatory gate.
        supports_orders=False,
        supports_conditional_orders=False,
        supports_investor_flow=False,
        supports_account_sync=True,
        supports_warnings=True,
    )

    def __init__(self, api: TossApiClient) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

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
        """`create`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
            audit_sink=audit_sink,
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
        """`get_quote`은(는) 필요한 데이터를 조회해 반환합니다."""

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
        """`get_candles`은(는) 필요한 데이터를 조회해 반환합니다."""

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
        """`get_orderbook`은(는) 필요한 데이터를 조회해 반환합니다."""

        payload = self._api.get("/api/v1/orderbook", group="MARKET_DATA", params={"symbol": symbol})
        result = _result_object(payload)
        return _levels(result, "asks"), _levels(result, "bids")

    def get_trades(self, symbol: str, limit: int = 20) -> list[Trade]:
        """`get_trades`은(는) 필요한 데이터를 조회해 반환합니다."""

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
        """`get_stock_info`은(는) 필요한 데이터를 조회해 반환합니다."""

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
        """`get_warnings`은(는) 필요한 데이터를 조회해 반환합니다."""

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
        """`get_accounts`은(는) 필요한 데이터를 조회해 반환합니다."""

        payload = self._api.get("/api/v1/accounts", group="ACCOUNT")
        return [_broker_account(row) for row in _result_list(payload)]

    def websocket_access_token(self) -> str:
        """토큰 값을 브라우저에 노출하지 않고 서버 실시간 연결에만 제공한다."""
        return self._api.access_token()

    def get_holdings(self, account_seq: int) -> HoldingsSnapshot:
        """`get_holdings`은(는) 필요한 데이터를 조회해 반환합니다."""

        payload = self._api.get("/api/v1/holdings", group="ASSET", account_seq=account_seq)
        result = _result_object(payload)
        return _holdings_snapshot(result, account_seq)

    def list_stocks(
        self,
        market: str,
        *,
        status: str = "ACTIVE",
        security_type: str | None = None,
        common_share: bool | None = None,
    ) -> list[dict[str, Any]]:
        """전체 종목 원장에서 시장별 종목을 조회한다."""
        params: dict[str, Any] = {"market": market, "status": status}
        if security_type is not None:
            params["securityType"] = security_type
        if common_share is not None:
            params["commonShare"] = common_share
        payload = self._api.get("/api/v1/stocks/all", group="STOCK_ALL", params=params)
        return _result_list(payload)

    def get_price_limit(self, symbol: str) -> dict[str, Any]:
        """당일 상·하한가와 가격 제한 여부를 조회한다."""
        payload = self._api.get(
            "/api/v1/price-limits",
            group="MARKET_DATA",
            params={"symbol": symbol},
        )
        return _result_object(payload)

    def get_exchange_rate(
        self,
        base_currency: str = "USD",
        quote_currency: str = "KRW",
    ) -> dict[str, Any]:
        """해외주식 원화 환산에 사용하는 참고 환율을 조회한다."""
        payload = self._api.get(
            "/api/v1/exchange-rate",
            group="MARKET_INFO",
            params={"baseCurrency": base_currency, "quoteCurrency": quote_currency},
        )
        return _result_object(payload)

    def get_market_calendar(self, country: str, target_date: date | None = None) -> dict[str, Any]:
        """한국 또는 미국 시장의 장 운영 시간과 휴장 여부를 조회한다."""
        normalized = country.strip().upper()
        if normalized not in {"KR", "US"}:
            raise ValueError("Toss market calendar country must be KR or US")
        params = {"date": target_date.isoformat()} if target_date else None
        payload = self._api.get(
            f"/api/v1/market-calendar/{normalized}",
            group="MARKET_INFO",
            params=params,
        )
        return _result_object(payload)

    def get_rankings(
        self,
        *,
        ranking_type: str,
        market_country: str,
        duration: str,
        count: int = 10,
        exclude_investment_caution: bool = True,
    ) -> dict[str, Any]:
        """거래대금·거래량·상승·하락 종목 순위를 조회한다."""
        payload = self._api.get(
            "/api/v1/rankings",
            group="RANKING",
            params={
                "type": ranking_type,
                "marketCountry": market_country,
                "duration": duration,
                "count": count,
                "excludeInvestmentCaution": exclude_investment_caution,
            },
        )
        return _result_object(payload)

    def get_market_indicator_prices(self, symbols: list[str]) -> list[dict[str, Any]]:
        """코스피·코스닥과 한국 국채 금리의 현재 값을 조회한다."""
        payload = self._api.get(
            "/api/v1/market-indicators/prices",
            group="MARKET_INDICATOR_PRICE",
            params={"symbols": ",".join(symbols)},
        )
        return _result_list(payload)

    def get_market_indicator_candles(
        self,
        symbol: str,
        *,
        interval: str = "1d",
        count: int = 30,
    ) -> dict[str, Any]:
        """시장 지수 또는 국채 금리의 시계열을 조회한다."""
        payload = self._api.get(
            f"/api/v1/market-indicators/{symbol}/candles",
            group="MARKET_INDICATOR_CHART",
            params={"interval": interval, "count": count},
        )
        return _result_object(payload)

    def get_market_indicator_investor_trading(
        self,
        symbol: str,
        *,
        interval: str = "1d",
        count: int = 10,
    ) -> dict[str, Any]:
        """코스피·코스닥의 투자자별 매매대금 흐름을 조회한다."""
        payload = self._api.get(
            f"/api/v1/market-indicators/{symbol}/investor-trading",
            group="MARKET_INDICATOR",
            params={"interval": interval, "count": count},
        )
        return _result_object(payload)

    def get_stock_trading_trend(
        self,
        symbol: str,
        trend: str,
        *,
        count: int = 20,
    ) -> dict[str, Any]:
        """국내 종목의 수급·프로그램·공매도·신용·대차 추이를 조회한다."""
        allowed = {
            "investor-trading",
            "program-trades",
            "short-selling",
            "credit-trades",
            "securities-lending",
        }
        if trend not in allowed:
            raise ValueError("Unsupported Toss stock trading trend")
        payload = self._api.get(
            f"/api/v1/stocks/{symbol}/{trend}",
            group="STOCK_TRADING_TREND",
            params={"count": count},
        )
        return _result_object(payload)

    def get_buying_power(self, account_seq: int, currency: str) -> dict[str, Any]:
        """실제 주문 전에 현금 기반 매수 가능 금액을 조회한다."""
        payload = self._api.get(
            "/api/v1/buying-power",
            group="ORDER_INFO",
            params={"currency": currency},
            account_seq=account_seq,
        )
        return _result_object(payload)

    def get_sellable_quantity(self, account_seq: int, symbol: str) -> dict[str, Any]:
        """계좌에서 현재 매도 가능한 종목 수량을 조회한다."""
        payload = self._api.get(
            "/api/v1/sellable-quantity",
            group="ORDER_INFO",
            params={"symbol": symbol},
            account_seq=account_seq,
        )
        return _result_object(payload)

    def get_commissions(self, account_seq: int) -> list[dict[str, Any]]:
        """계좌에 적용되는 국내·미국 시장 수수료를 조회한다."""
        payload = self._api.get(
            "/api/v1/commissions",
            group="ORDER_INFO",
            account_seq=account_seq,
        )
        return _result_list(payload)

    def get_orders(
        self,
        account_seq: int,
        *,
        status: str,
        symbol: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """진행 중이거나 종료된 실제 주문 목록을 조회한다."""
        params: dict[str, Any] = {"status": status, "limit": limit}
        if symbol:
            params["symbol"] = symbol
        payload = self._api.get(
            "/api/v1/orders",
            group="ORDER_HISTORY",
            params=params,
            account_seq=account_seq,
        )
        return _result_object(payload)

    def get_order(self, account_seq: int, order_id: str) -> dict[str, Any]:
        """실제 주문 한 건의 상태와 부분 체결 내역을 조회한다."""
        payload = self._api.get(
            f"/api/v1/orders/{order_id}",
            group="ORDER_HISTORY",
            account_seq=account_seq,
        )
        return _result_object(payload)

    def create_order(self, account_seq: int, order: dict[str, Any]) -> dict[str, Any]:
        """검증된 실제 주문 요청을 토스에 전달한다."""
        payload = self._api.request(
            "POST",
            "/api/v1/orders",
            group="ORDER",
            json=order,
            account_seq=account_seq,
        )
        return _result_object(payload)

    def modify_order(
        self, account_seq: int, order_id: str, changes: dict[str, Any]
    ) -> dict[str, Any]:
        """미체결 실제 주문의 가격 또는 수량을 정정한다."""
        payload = self._api.request(
            "POST",
            f"/api/v1/orders/{order_id}/modify",
            group="ORDER",
            json=changes,
            account_seq=account_seq,
        )
        return _result_object(payload)

    def cancel_order(self, account_seq: int, order_id: str) -> dict[str, Any]:
        """미체결 실제 주문을 취소한다."""
        payload = self._api.request(
            "POST",
            f"/api/v1/orders/{order_id}/cancel",
            group="ORDER",
            json={},
            account_seq=account_seq,
        )
        return _result_object(payload)

    def get_conditional_orders(
        self,
        account_seq: int,
        *,
        status: str,
        symbol: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """진행 중이거나 종료된 조건주문 목록을 조회한다."""
        params: dict[str, Any] = {"status": status, "limit": limit}
        if symbol:
            params["symbol"] = symbol
        payload = self._api.get(
            "/api/v1/conditional-orders",
            group="CONDITIONAL_ORDER_HISTORY",
            params=params,
            account_seq=account_seq,
        )
        return _result_object(payload)

    def get_conditional_order(
        self, account_seq: int, conditional_order_id: str
    ) -> dict[str, Any]:
        """조건주문 한 건의 감시·체결 상태를 조회한다."""
        payload = self._api.get(
            f"/api/v1/conditional-orders/{conditional_order_id}",
            group="CONDITIONAL_ORDER_HISTORY",
            account_seq=account_seq,
        )
        return _result_object(payload)

    def create_conditional_order(
        self, account_seq: int, order: dict[str, Any]
    ) -> dict[str, Any]:
        """검증된 실제 조건주문을 등록한다."""
        payload = self._api.request(
            "POST",
            "/api/v1/conditional-orders",
            group="CONDITIONAL_ORDER",
            json=order,
            account_seq=account_seq,
        )
        return _result_object(payload)

    def modify_conditional_order(
        self,
        account_seq: int,
        conditional_order_id: str,
        changes: dict[str, Any],
    ) -> dict[str, Any]:
        """실제 조건주문의 감시 조건과 주문 조건을 수정한다."""
        payload = self._api.request(
            "POST",
            f"/api/v1/conditional-orders/{conditional_order_id}/modify",
            group="CONDITIONAL_ORDER",
            json=changes,
            account_seq=account_seq,
        )
        return _result_object(payload)

    def cancel_conditional_order(
        self, account_seq: int, conditional_order_id: str
    ) -> dict[str, Any]:
        """아직 종료되지 않은 실제 조건주문을 취소한다."""
        payload = self._api.request(
            "DELETE",
            f"/api/v1/conditional-orders/{conditional_order_id}",
            group="CONDITIONAL_ORDER",
            account_seq=account_seq,
        )
        return _result_object(payload)

    def close(self) -> None:
        """`close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        self._api.close()


def _result_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """`_result_list`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    result = payload.get("result")
    if not isinstance(result, list) or not all(isinstance(item, dict) for item in result):
        raise ProviderUnavailableError(
            "Toss returned an invalid result array", code="invalid-provider-response"
        )
    return result


def _result_object(payload: dict[str, Any]) -> dict[str, Any]:
    """`_result_object`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    result = payload.get("result")
    if not isinstance(result, dict):
        raise ProviderUnavailableError(
            "Toss returned an invalid result object", code="invalid-provider-response"
        )
    return result


def _find_symbol(rows: list[dict[str, Any]], symbol: str) -> dict[str, Any]:
    """`_find_symbol`은(는) 필요한 데이터를 조회해 반환합니다."""

    for row in rows:
        if row.get("symbol") == symbol:
            return row
    raise ProviderNotFoundError(f"Toss did not return stock {symbol}", code="stock-not-found")


def _candle(row: dict[str, Any]) -> Candle:
    """`_candle`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return Candle(
        timestamp=_required_datetime(row.get("timestamp")),
        open=_decimal(row, "openPrice"),
        high=_decimal(row, "highPrice"),
        low=_decimal(row, "lowPrice"),
        close=_decimal(row, "closePrice"),
        volume=_integer_decimal(row, "volume"),
        price_basis="provider_adjusted",
    )


def _levels(result: dict[str, Any], key: str) -> list[OrderbookLevel]:
    """`_levels`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
    """`_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    try:
        return Decimal(str(row[key]))
    except (KeyError, InvalidOperation, TypeError) as exc:
        raise ProviderUnavailableError(
            f"Toss returned an invalid decimal field: {key}",
            code="invalid-provider-response",
        ) from exc


def _integer_decimal(row: dict[str, Any], key: str) -> int:
    """`_integer_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    value = _decimal(row, key)
    if value != value.to_integral_value():
        raise ProviderUnavailableError(
            f"Toss returned a fractional {key} unsupported by the KRX domain",
            code="unsupported-fractional-volume",
        )
    return int(value)


def _required_datetime(value: Any) -> datetime:
    """`_required_datetime`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    parsed = _optional_datetime(value)
    if parsed is None:
        raise ProviderUnavailableError(
            "Toss response omitted a required timestamp", code="invalid-provider-response"
        )
    return parsed


def _optional_datetime(value: Any) -> datetime | None:
    """`_optional_datetime`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
    """`_optional_date`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if value is None:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ProviderUnavailableError(
            "Toss returned an invalid date", code="invalid-provider-response"
        ) from exc


def _optional_string(value: Any) -> str | None:
    """`_optional_string`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return None if value is None else str(value)


def _broker_account(row: dict[str, Any]) -> BrokerAccount:
    """`_broker_account`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
    """`_holdings_snapshot`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
    """`_holding`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
    """`_required_object`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    value = row.get(key)
    if not isinstance(value, dict):
        raise ProviderUnavailableError(
            f"Toss returned an invalid object field: {key}",
            code="invalid-provider-response",
        )
    return value


def _currency_totals(row: dict[str, Any]) -> dict[str, Decimal | None]:
    """`_currency_totals`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return {"KRW": _optional_decimal(row, "krw"), "USD": _optional_decimal(row, "usd")}


def _optional_decimal(row: dict[str, Any], key: str) -> Decimal | None:
    """`_optional_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if row.get(key) is None:
        return None
    return _decimal(row, key)
