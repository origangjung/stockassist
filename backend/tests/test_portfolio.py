from decimal import Decimal

import httpx2
import pytest

from app.adapters.broker import BrokerAdapter
from app.providers.errors import ProviderForbiddenError
from app.providers.mock import MockProvider
from app.providers.toss.provider import TossProvider
from app.repositories.memory import InMemoryPortfolioRepository
from app.services.portfolio import PortfolioService


def test_portfolio_sync_keeps_krw_and_usd_exposure_separate_and_masks_account_number():
    repository = InMemoryPortfolioRepository()
    service = PortfolioService(
        BrokerAdapter([MockProvider()]), sync_enabled=True, repository=repository
    )

    accounts = service.accounts()
    synced = service.sync(1)

    assert accounts["accounts"][0]["account_no_masked"].endswith("8901")
    assert synced["is_read_only"] is True
    assert synced["analysis"]["currency_separated"] is True
    assert synced["analysis"]["analysis_version"] == "portfolio-2026.2"
    assert synced["analysis"]["execution_enabled"] is False
    assert synced["analysis"]["reference_signal"] == "concentration_watch"
    assert synced["analysis"]["currencies"]["KRW"]["concentration_index"] == 1
    assert synced["analysis"]["currencies"]["USD"]["effective_holding_count"] == 1
    assert {holding["currency"] for holding in synced["holdings"]} == {"KRW", "USD"}
    assert synced["persistence_status"] == "saved"
    assert len(repository.snapshots) == 1


def test_portfolio_sync_is_disabled_until_explicitly_enabled():
    service = PortfolioService(BrokerAdapter([MockProvider()]), sync_enabled=False)

    with pytest.raises(ProviderForbiddenError, match="disabled"):
        service.accounts()


def test_toss_provider_maps_accounts_and_holdings_using_account_header():
    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path == "/oauth2/token":
            return httpx2.Response(200, json={"access_token": "token", "expires_in": 3600})
        assert request.headers["Authorization"] == "Bearer token"
        if request.url.path == "/api/v1/accounts":
            return httpx2.Response(
                200,
                json={
                    "result": [
                        {"accountNo": "12345678901", "accountSeq": 1, "accountType": "BROKERAGE"}
                    ]
                },
            )
        assert request.url.path == "/api/v1/holdings"
        assert request.headers["X-Tossinvest-Account"] == "1"
        return httpx2.Response(
            200,
            json={
                "result": {
                    "totalPurchaseAmount": {"krw": "6500000", "usd": "1553"},
                    "marketValue": {
                        "amount": {"krw": "7200000", "usd": "1785"},
                        "amountAfterCost": {"krw": "7050000", "usd": "1771.43"},
                    },
                    "profitLoss": {
                        "amount": {"krw": "700000", "usd": "232"},
                        "amountAfterCost": {"krw": "550000", "usd": "218.43"},
                        "rate": "0.1179",
                        "rateAfterCost": "0.0983",
                    },
                    "dailyProfitLoss": {"amount": {"krw": "100000", "usd": "25"}, "rate": "0.0141"},
                    "items": [
                        {
                            "symbol": "AAPL",
                            "name": "Apple Inc.",
                            "marketCountry": "US",
                            "currency": "USD",
                            "quantity": "10",
                            "lastPrice": "178.5",
                            "averagePurchasePrice": "155.3",
                            "marketValue": {
                                "purchaseAmount": "1553",
                                "amount": "1785",
                                "amountAfterCost": "1771.43",
                            },
                            "profitLoss": {
                                "amount": "232",
                                "amountAfterCost": "218.43",
                                "rate": "0.1494",
                                "rateAfterCost": "0.1406",
                            },
                            "dailyProfitLoss": {"amount": "25", "rate": "0.0142"},
                            "cost": {"commission": "3.57", "tax": "10"},
                        }
                    ],
                }
            },
        )

    provider = TossProvider.create(
        base_url="https://openapi.tossinvest.com",
        client_id="client",
        client_secret="secret",
        transport=httpx2.MockTransport(handler),
    )
    try:
        account = provider.get_accounts()[0]
        snapshot = provider.get_holdings(account.account_seq)
    finally:
        provider.close()

    assert account.account_type == "BROKERAGE"
    assert snapshot.market_value["USD"] == Decimal("1785")
    assert snapshot.holdings[0].symbol == "AAPL"
