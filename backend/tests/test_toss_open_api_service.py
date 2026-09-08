from unittest.mock import Mock
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.providers.errors import ProviderForbiddenError, ProviderUnavailableError
from app.services.toss_open_api import TossOpenApiService
from app.providers.contracts import OrderbookLevel, Trade


def test_stock_search_uses_available_markets_when_one_catalog_call_fails():
    provider = Mock()
    provider.name = "toss"

    def list_stocks(market: str):
        if market == "KOSPI":
            return [{"symbol": "005930", "name": "삼성전자", "englishName": "Samsung"}]
        if market == "NYSE":
            raise ProviderUnavailableError("temporary")
        return []

    provider.list_stocks.side_effect = list_stocks
    service = TossOpenApiService(provider)

    result = service.search_stocks("삼성", 5)

    assert result["catalog_size"] == 1
    assert result["items"][0]["symbol"] == "005930"


def test_market_overview_is_partial_when_one_public_endpoint_fails():
    provider = Mock()
    provider.name = "toss"
    provider.get_market_indicator_prices.return_value = []
    provider.get_exchange_rate.side_effect = ProviderUnavailableError("temporary")
    provider.get_market_calendar.return_value = {"isBusinessDay": True}
    provider.get_rankings.return_value = {"rankedAt": None, "rankings": []}
    service = TossOpenApiService(provider)

    result = service.market_overview()

    assert result["exchange_rate"] is None
    assert result["calendars"]["KR"]["isBusinessDay"] is True
    assert result["partial_errors"]["exchange_rate"]["code"] == "provider-error"


def test_real_order_is_denied_until_both_server_gate_and_confirmation_match():
    provider = Mock()
    service = TossOpenApiService(
        provider,
        account_access_enabled=True,
        trading_enabled=False,
    )

    with pytest.raises(ProviderForbiddenError) as caught:
        service.submit_order(1, {"symbol": "005930"}, confirmation="실제 주문 실행")

    assert caught.value.code == "toss-trading-disabled"
    provider.create_order.assert_not_called()


def test_stock_microstructure_includes_buying_and_selling_pressure():
    provider = Mock()
    provider.name = "toss"
    provider.get_orderbook.return_value = (
        [OrderbookLevel(Decimal("101"), Decimal("100"))],
        [OrderbookLevel(Decimal("100"), Decimal("300"))],
    )
    provider.get_trades.return_value = [
        Trade(
            "AAPL",
            Decimal("101"),
            Decimal("50"),
            "buy",
            datetime(2026, 8, 22, tzinfo=timezone.utc),
        )
    ]
    provider.get_price_limit.return_value = {}
    provider.get_warnings.return_value = []

    result = TossOpenApiService(provider).stock_microstructure("AAPL")

    assert result["pressure"]["signal"] == "buying"
    assert result["pressure"]["source"] == "trades_and_orderbook"
