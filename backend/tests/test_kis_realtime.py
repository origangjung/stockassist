import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal

import httpx2
import pytest

from app.providers.contracts import StockInfo
from app.adapters.broker import BrokerAdapter
from app.config.settings import Settings
from app.providers.errors import ProviderValidationError
from app.providers.mock import MockProvider
from app.realtime.factory import build_realtime_quote_hub
from app.realtime.kis import (
    DOMESTIC_FIELD_COUNT,
    DOMESTIC_TR_ID,
    OVERSEAS_FIELD_COUNT,
    OVERSEAS_TR_ID,
    KISStreamingQuoteSource,
    parse_realtime_quotes,
    resolve_subscription,
    subscription_message,
)


def test_subscription_contract_supports_domestic_and_us_markets():
    domestic = resolve_subscription(MockProvider().get_stock_info("005930"))
    nasdaq = resolve_subscription(MockProvider().get_stock_info("AAPL"))
    nyse = resolve_subscription(MockProvider().get_stock_info("JPM"))

    assert (domestic.tr_id, domestic.tr_key) == (DOMESTIC_TR_ID, "005930")
    assert (nasdaq.tr_id, nasdaq.tr_key) == (OVERSEAS_TR_ID, "DNASAAPL")
    assert (nyse.tr_id, nyse.tr_key) == (OVERSEAS_TR_ID, "DNYSJPM")
    message = subscription_message("approval", nasdaq, "1")
    assert message["header"]["approval_key"] == "approval"
    assert message["header"]["tr_type"] == "1"
    assert message["body"]["input"] == {"tr_id": OVERSEAS_TR_ID, "tr_key": "DNASAAPL"}


def test_unsupported_exchange_is_rejected_before_websocket_subscription():
    stock = StockInfo("TEST", "Test", "LSE", None, None, "USD")

    with pytest.raises(ProviderValidationError, match="exchange code"):
        resolve_subscription(stock)


def test_domestic_and_overseas_messages_are_normalized_to_quote_contract():
    domestic = resolve_subscription(MockProvider().get_stock_info("005930"))
    domestic_fields = ["0"] * DOMESTIC_FIELD_COUNT
    domestic_fields[0] = "005930"
    domestic_fields[1] = "101530"
    domestic_fields[2] = "74800"
    domestic_fields[3] = "4"
    domestic_fields[4] = "1200"
    domestic_fields[5] = "1.58"
    domestic_fields[13] = "14201392"
    domestic_fields[33] = "20260715"
    domestic_raw = f"0|{DOMESTIC_TR_ID}|1|{'^'.join(domestic_fields)}"

    overseas = resolve_subscription(MockProvider().get_stock_info("AAPL"))
    overseas_fields = ["0"] * OVERSEAS_FIELD_COUNT
    overseas_fields[0] = "DNASAAPL"
    overseas_fields[3] = "20260715"
    overseas_fields[4] = "103000"
    overseas_fields[10] = "214.15"
    overseas_fields[11] = "2"
    overseas_fields[12] = "1.82"
    overseas_fields[13] = "0.86"
    overseas_fields[19] = "54182000"
    overseas_raw = f"0|{OVERSEAS_TR_ID}|1|{'^'.join(overseas_fields)}"

    domestic_quote = parse_realtime_quotes(
        domestic_raw, {(domestic.tr_id, domestic.tr_key): domestic}
    )[0]
    overseas_quote = parse_realtime_quotes(
        overseas_raw, {(overseas.tr_id, overseas.tr_key): overseas}
    )[0]

    assert domestic_quote.price == Decimal("74800")
    assert domestic_quote.change == Decimal("-1200")
    assert domestic_quote.change_percent == Decimal("-1.58")
    assert domestic_quote.volume == 14_201_392
    assert domestic_quote.as_of == datetime(2026, 7, 15, 1, 15, 30, tzinfo=UTC)
    assert overseas_quote.symbol == "AAPL"
    assert overseas_quote.currency == "USD"
    assert overseas_quote.price == Decimal("214.15")


def test_malformed_realtime_message_is_rejected():
    subscription = resolve_subscription(MockProvider().get_stock_info("005930"))
    raw = f"0|{DOMESTIC_TR_ID}|1|005930^101530"

    with pytest.raises(ProviderValidationError, match="insufficient fields"):
        parse_realtime_quotes(raw, {(subscription.tr_id, subscription.tr_key): subscription})


def test_approval_key_is_requested_once_and_cached():
    requests = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal requests
        requests += 1
        assert request.url.path == "/oauth2/Approval"
        assert json.loads(request.content) == {
            "grant_type": "client_credentials",
            "appkey": "app-key",
            "secretkey": "app-secret",
        }
        return httpx2.Response(200, json={"approval_key": "approval-key"})

    async def scenario() -> None:
        source = KISStreamingQuoteSource(
            base_url="https://example.test",
            websocket_url="ws://example.test/tryitout",
            app_key="app-key",
            app_secret="app-secret",
            resolver=MockProvider(),
            transport=httpx2.MockTransport(handler),
        )
        assert await source.get_approval_key() == "approval-key"
        assert await source.get_approval_key() == "approval-key"
        await source.stop()

    asyncio.run(scenario())
    assert requests == 1


def test_kis_realtime_factory_requires_credentials():
    settings = Settings(
        _env_file=None,
        realtime_source="kis",
        kis_app_key=None,
        kis_app_secret=None,
    )

    with pytest.raises(ValueError, match="KIS_APP_KEY"):
        build_realtime_quote_hub(settings, BrokerAdapter([MockProvider()]))
