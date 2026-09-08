"""토스증권의 확장 시장 데이터를 사용자용 읽기 모델로 조립한다."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from collections.abc import Callable
from threading import Lock
from time import monotonic
from typing import Any

from app.microstructure import calculate_market_pressure

from app.providers.errors import ProviderError, ProviderForbiddenError, ProviderUnavailableError
from app.providers.toss.provider import TossProvider


TOSS_STOCK_MARKETS = ("KOSPI", "KOSDAQ", "NYSE", "NASDAQ", "AMEX", "KR_ETC", "US_ETC")
TOSS_INDICATOR_SYMBOLS = (
    "KOSPI",
    "KOSDAQ",
    "KR_BOND_2Y",
    "KR_BOND_3Y",
    "KR_BOND_5Y",
    "KR_BOND_10Y",
    "KR_BOND_20Y",
    "KR_BOND_30Y",
)


class TossOpenApiService:
    """공식 토스 Open API를 화면에서 사용하기 좋은 읽기 전용 계약으로 제공한다."""

    def __init__(
        self,
        provider: TossProvider | None,
        *,
        account_access_enabled: bool = False,
        trading_enabled: bool = False,
        catalog_ttl_seconds: float = 21_600,
    ) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._provider = provider
        self._account_access_enabled = account_access_enabled
        self._trading_enabled = trading_enabled
        self._catalog_ttl_seconds = max(60.0, catalog_ttl_seconds)
        self._catalog: tuple[dict[str, Any], ...] = ()
        self._catalog_expires_at = 0.0
        self._catalog_lock = Lock()

    @property
    def available(self) -> bool:
        """`available`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        return self._provider is not None

    def search_stocks(self, query: str, limit: int = 12) -> dict[str, Any]:
        """`search_stocks`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        normalized = _normalize_search(query)
        if not normalized:
            return {"provider": "toss", "items": [], "catalog_size": 0}
        catalog = self._stock_catalog()
        ranked: list[tuple[int, int, dict[str, Any]]] = []
        for index, stock in enumerate(catalog):
            candidates = (
                str(stock.get("symbol") or ""),
                str(stock.get("name") or ""),
                str(stock.get("englishName") or ""),
            )
            normalized_candidates = tuple(_normalize_search(value) for value in candidates)
            if normalized in normalized_candidates:
                rank = 0
            elif any(value.startswith(normalized) for value in normalized_candidates):
                rank = 1
            elif any(normalized in value for value in normalized_candidates):
                rank = 2
            else:
                continue
            ranked.append((rank, index, stock))
        ranked.sort(key=lambda item: (item[0], item[1]))
        return {
            "provider": "toss",
            "items": [item[2] for item in ranked[:limit]],
            "catalog_size": len(catalog),
        }

    def market_overview(self) -> dict[str, Any]:
        """`market_overview`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        provider = self._require_provider()
        errors: dict[str, dict[str, Any]] = {}
        return {
            "provider": provider.name,
            "indicators": self._attempt(
                "indicators",
                lambda: provider.get_market_indicator_prices(list(TOSS_INDICATOR_SYMBOLS)),
                errors,
                [],
            ),
            "exchange_rate": self._attempt(
                "exchange_rate", provider.get_exchange_rate, errors, None
            ),
            "calendars": {
                country: self._attempt(
                    f"calendar_{country}",
                    lambda country=country: provider.get_market_calendar(country, date.today()),
                    errors,
                    None,
                )
                for country in ("KR", "US")
            },
            "rankings": {
                country: self._attempt(
                    f"ranking_{country}",
                    lambda country=country: provider.get_rankings(
                        ranking_type="MARKET_TRADING_AMOUNT",
                        market_country=country,
                        duration="1d",
                    ),
                    errors,
                    {"rankedAt": None, "rankings": []},
                )
                for country in ("KR", "US")
            },
            "partial_errors": errors,
        }

    def rankings(
        self,
        ranking_type: str,
        market_country: str,
        duration: str,
        count: int,
    ) -> dict[str, Any]:
        """공식 랭킹의 지원 조합을 그대로 전달하는 읽기 전용 진입점이다."""
        provider = self._require_provider()
        return {
            "provider": provider.name,
            "type": ranking_type,
            "market_country": market_country,
            "duration": duration,
            **provider.get_rankings(
                ranking_type=ranking_type,
                market_country=market_country,
                duration=duration,
                count=count,
            ),
        }

    def market_indicator_history(
        self,
        symbol: str,
        *,
        interval: str,
        count: int,
    ) -> dict[str, Any]:
        """지수·국채 캔들과 지원되는 투자자 매매 흐름을 묶어 반환한다."""
        provider = self._require_provider()
        errors: dict[str, dict[str, Any]] = {}
        investor_trading = None
        if symbol in {"KOSPI", "KOSDAQ"}:
            investor_trading = self._attempt(
                "investor_trading",
                lambda: provider.get_market_indicator_investor_trading(
                    symbol, interval=interval, count=count
                ),
                errors,
                None,
            )
        return {
            "provider": provider.name,
            "symbol": symbol,
            "candles": provider.get_market_indicator_candles(
                symbol, interval=interval, count=count
            ),
            "investor_trading": investor_trading,
            "partial_errors": errors,
        }

    def stock_microstructure(self, symbol: str, trade_limit: int = 20) -> dict[str, Any]:
        """`stock_microstructure`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        provider = self._require_provider()
        asks, bids = provider.get_orderbook(symbol)
        trades = provider.get_trades(symbol, trade_limit)
        return {
            "provider": provider.name,
            "price_limit": provider.get_price_limit(symbol),
            "orderbook": {
                "asks": [{"price": item.price, "quantity": item.quantity} for item in asks],
                "bids": [{"price": item.price, "quantity": item.quantity} for item in bids],
            },
            "trades": [
                {
                    "symbol": item.symbol,
                    "price": item.price,
                    "quantity": item.quantity,
                    "side": item.side,
                    "executed_at": item.executed_at,
                }
                for item in trades
            ],
            "pressure": calculate_market_pressure(asks, bids, trades),
            "warnings": [
                {
                    "warning_type": item.warning_type,
                    "exchange": item.exchange,
                    "start_date": item.start_date,
                    "end_date": item.end_date,
                }
                for item in provider.get_warnings(symbol)
            ],
        }

    def stock_trends(self, symbol: str, count: int = 20) -> dict[str, Any]:
        """`stock_trends`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        provider = self._require_provider()
        return {
            "provider": provider.name,
            "investor_trading": provider.get_stock_trading_trend(
                symbol, "investor-trading", count=count
            ),
            "program_trades": provider.get_stock_trading_trend(
                symbol, "program-trades", count=count
            ),
            "short_selling": provider.get_stock_trading_trend(
                symbol, "short-selling", count=count
            ),
            "credit_trades": provider.get_stock_trading_trend(
                symbol, "credit-trades", count=count
            ),
            "securities_lending": provider.get_stock_trading_trend(
                symbol, "securities-lending", count=count
            ),
        }

    def account_workspace(
        self,
        account_seq: int,
        *,
        symbol: str | None = None,
        currency: str = "KRW",
    ) -> dict[str, Any]:
        """보유 자산과 실제 주문 전 확인 정보를 읽기 전용으로 묶는다."""
        provider = self._require_account_access()
        errors: dict[str, dict[str, Any]] = {}
        holdings = self._attempt(
            "holdings", lambda: provider.get_holdings(account_seq), errors, None
        )
        payload: dict[str, Any] = {
            "provider": provider.name,
            "holdings": asdict(holdings) if holdings is not None else None,
            "buying_power": self._attempt(
                "buying_power",
                lambda: provider.get_buying_power(account_seq, currency),
                errors,
                None,
            ),
            "commissions": self._attempt(
                "commissions",
                lambda: provider.get_commissions(account_seq),
                errors,
                [],
            ),
            "orders": {
                status.lower(): self._attempt(
                    f"orders_{status.lower()}",
                    lambda status=status: provider.get_orders(
                        account_seq, status=status, symbol=symbol
                    ),
                    errors,
                    {"orders": [], "nextCursor": None},
                )
                for status in ("OPEN", "CLOSED")
            },
            "conditional_orders": {
                status.lower(): self._attempt(
                    f"conditional_orders_{status.lower()}",
                    lambda status=status: provider.get_conditional_orders(
                        account_seq, status=status, symbol=symbol
                    ),
                    errors,
                    {"conditionalOrders": [], "nextCursor": None},
                )
                for status in ("OPEN", "CLOSED")
            },
            "trading_enabled": self._trading_enabled,
            "partial_errors": errors,
        }
        if symbol:
            payload["sellable_quantity"] = self._attempt(
                "sellable_quantity",
                lambda: provider.get_sellable_quantity(account_seq, symbol),
                errors,
                None,
            )
        return payload

    def order_detail(self, account_seq: int, order_id: str) -> dict[str, Any]:
        """부분 체결을 포함한 실제 주문 한 건을 읽기 전용으로 조회한다."""
        provider = self._require_account_access()
        return provider.get_order(account_seq, order_id)

    def conditional_order_detail(
        self, account_seq: int, conditional_order_id: str
    ) -> dict[str, Any]:
        """조건 감시 상태를 포함한 조건주문 한 건을 읽기 전용으로 조회한다."""
        provider = self._require_account_access()
        return provider.get_conditional_order(account_seq, conditional_order_id)

    def submit_order(
        self,
        account_seq: int,
        order: dict[str, Any],
        *,
        confirmation: str,
    ) -> dict[str, Any]:
        """`submit_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        provider = self._require_trading(confirmation)
        return provider.create_order(account_seq, order)

    def modify_order(
        self,
        account_seq: int,
        order_id: str,
        changes: dict[str, Any],
        *,
        confirmation: str,
    ) -> dict[str, Any]:
        """`modify_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        provider = self._require_trading(confirmation)
        return provider.modify_order(account_seq, order_id, changes)

    def cancel_order(
        self, account_seq: int, order_id: str, *, confirmation: str
    ) -> dict[str, Any]:
        """`cancel_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        provider = self._require_trading(confirmation)
        return provider.cancel_order(account_seq, order_id)

    def submit_conditional_order(
        self,
        account_seq: int,
        order: dict[str, Any],
        *,
        confirmation: str,
    ) -> dict[str, Any]:
        """`submit_conditional_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        provider = self._require_trading(confirmation)
        return provider.create_conditional_order(account_seq, order)

    def modify_conditional_order(
        self,
        account_seq: int,
        conditional_order_id: str,
        changes: dict[str, Any],
        *,
        confirmation: str,
    ) -> dict[str, Any]:
        """`modify_conditional_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        provider = self._require_trading(confirmation)
        return provider.modify_conditional_order(account_seq, conditional_order_id, changes)

    def cancel_conditional_order(
        self,
        account_seq: int,
        conditional_order_id: str,
        *,
        confirmation: str,
    ) -> dict[str, Any]:
        """`cancel_conditional_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        provider = self._require_trading(confirmation)
        return provider.cancel_conditional_order(account_seq, conditional_order_id)

    def _stock_catalog(self) -> tuple[dict[str, Any], ...]:
        """`_stock_catalog`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        now = monotonic()
        if self._catalog and self._catalog_expires_at > now:
            return self._catalog
        with self._catalog_lock:
            now = monotonic()
            if self._catalog and self._catalog_expires_at > now:
                return self._catalog
            provider = self._require_provider()
            stocks: list[dict[str, Any]] = []
            last_error: ProviderError | None = None
            for market in TOSS_STOCK_MARKETS:
                try:
                    for stock in provider.list_stocks(market):
                        # stocks/all은 시장을 쿼리로 받기 때문에 응답에서 market·currency를
                        # 생략할 수 있다. 화면 계약에는 조회 문맥을 명시적으로 보존한다.
                        enriched = dict(stock)
                        enriched.setdefault("market", market)
                        enriched.setdefault(
                            "currency",
                            "KRW" if market in {"KOSPI", "KOSDAQ", "KR_ETC"} else "USD",
                        )
                        enriched.setdefault("status", "ACTIVE")
                        stocks.append(enriched)
                except ProviderError as exc:
                    # 한 시장의 일시 오류가 다른 시장의 검색까지 막지 않게 한다.
                    last_error = exc
            if not stocks and last_error is not None:
                raise last_error
            deduplicated = {str(stock.get("symbol")): stock for stock in stocks}
            self._catalog = tuple(deduplicated.values())
            self._catalog_expires_at = now + self._catalog_ttl_seconds
            return self._catalog

    @staticmethod
    def _attempt(
        name: str,
        operation: Callable[[], Any],
        errors: dict[str, dict[str, Any]],
        fallback: Any,
    ) -> Any:
        """복합 화면에서 일부 공급자 오류를 비밀정보 없는 상태값으로 격리한다."""
        try:
            return operation()
        except ProviderError as exc:
            errors[name] = {"code": exc.code, "status_code": exc.status_code}
            return fallback

    def _require_provider(self) -> TossProvider:
        """`_require_provider`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        if self._provider is None:
            raise ProviderUnavailableError(
                "Toss Open API provider is not active",
                code="toss-provider-inactive",
                status_code=503,
            )
        return self._provider

    def _require_account_access(self) -> TossProvider:
        """`_require_account_access`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        provider = self._require_provider()
        if not self._account_access_enabled:
            raise ProviderForbiddenError(
                "Toss account access is disabled",
                code="toss-account-access-disabled",
                status_code=403,
            )
        return provider

    def _require_trading(self, confirmation: str) -> TossProvider:
        """`_require_trading`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        provider = self._require_account_access()
        if not self._trading_enabled:
            raise ProviderForbiddenError(
                "Real Toss trading is disabled",
                code="toss-trading-disabled",
                status_code=403,
            )
        if confirmation != "실제 주문 실행":
            raise ProviderForbiddenError(
                "Real order confirmation phrase does not match",
                code="toss-order-confirmation-required",
                status_code=403,
            )
        return provider


def _normalize_search(value: str) -> str:
    """`_normalize_search`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    return "".join(value.upper().split())
