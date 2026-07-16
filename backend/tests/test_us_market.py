from decimal import Decimal

import httpx2

from app.providers.mock import MockProvider
from app.providers.toss.provider import TossProvider


def test_mock_provider_supports_us_symbols_with_usd_precision():
    provider = MockProvider()

    quote = provider.get_quote("AAPL")
    candles = provider.get_candles("AAPL", 5)
    stock = provider.get_stock_info("JPM")

    assert quote.currency == "USD"
    assert quote.price.as_tuple().exponent == -2
    assert any(candle.close.as_tuple().exponent == -2 for candle in candles)
    assert stock.market == "NYSE"
    assert stock.currency == "USD"


def test_toss_provider_maps_us_stock_currency_and_fractional_trade_quantity():
    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path == "/oauth2/token":
            return httpx2.Response(
                200,
                json={
                    "access_token": "test-token",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                },
            )
        if request.url.path == "/api/v1/prices":
            assert request.url.params["symbols"] == "AAPL"
            return httpx2.Response(
                200,
                json={
                    "result": [
                        {
                            "symbol": "AAPL",
                            "lastPrice": "214.15",
                            "currency": "USD",
                            "timestamp": "2026-07-13T14:30:00-04:00",
                        }
                    ]
                },
            )
        if request.url.path == "/api/v1/stocks":
            return httpx2.Response(
                200,
                json={
                    "result": [
                        {
                            "symbol": "AAPL",
                            "name": "Apple",
                            "market": "NASDAQ",
                            "currency": "USD",
                            "listDate": "1980-12-12",
                        }
                    ]
                },
            )
        if request.url.path == "/api/v1/trades":
            return httpx2.Response(
                200,
                json={
                    "result": [
                        {
                            "price": "214.15",
                            "volume": "0.25",
                            "currency": "USD",
                            "timestamp": "2026-07-13T14:30:00-04:00",
                        }
                    ]
                },
            )
        raise AssertionError(f"unexpected path: {request.url.path}")

    provider = TossProvider.create(
        base_url="https://openapi.tossinvest.com",
        client_id="client",
        client_secret="secret",
        transport=httpx2.MockTransport(handler),
    )
    try:
        quote = provider.get_quote("AAPL")
        trades = provider.get_trades("AAPL", 1)
    finally:
        provider.close()

    assert quote.currency == "USD"
    assert quote.price == Decimal("214.15")
    assert trades[0].quantity == Decimal("0.25")
