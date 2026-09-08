from datetime import date
from decimal import Decimal

import httpx2
import pytest

from app.investor_flow.kis import KisInvestorFlowProvider
from app.investor_flow.providers import MockInvestorFlowProvider
from app.providers.errors import ProviderValidationError
from app.repositories.memory import InMemoryInvestorFlowRepository
from app.services.investor_flow import InvestorFlowService


def test_mock_investor_flow_is_persisted_and_labeled_as_reference_signal():
    repository = InMemoryInvestorFlowRepository()
    result = InvestorFlowService(MockInvestorFlowProvider(), repository).snapshot("005930")

    assert result["experimental"] is True
    assert result["reference_signal"] == "net_inflow"
    assert result["foreign_institution_net_quantity"] == Decimal("1160000")
    assert result["persistence_status"] == "saved"
    assert len(repository.items) == 1


def test_kis_provider_maps_investor_snapshot_and_caches_token():
    calls = {"token": 0, "flow": 0}

    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path == "/oauth2/tokenP":
            calls["token"] += 1
            assert b'"appkey":"app-key"' in request.content
            return httpx2.Response(200, json={"access_token": "kis-token", "expires_in": 3600})
        assert request.url.path == "/uapi/domestic-stock/v1/quotations/inquire-investor"
        calls["flow"] += 1
        assert request.headers["authorization"] == "Bearer kis-token"
        assert request.headers["tr_id"] == "FHKST01010900"
        assert request.url.params["FID_INPUT_ISCD"] == "005930"
        return httpx2.Response(
            200,
            json={
                "rt_cd": "0",
                "output": {
                    "frgn_ntby_qty": "1,250",
                    "orgn_ntby_qty": "-200",
                    "prsn_ntby_qty": "-1,050",
                    "frgn_hldn_qty": "300,000",
                    "frgn_hldn_rate": "51.23",
                },
            },
        )

    provider = KisInvestorFlowProvider.create(
        base_url="https://openapi.koreainvestment.com:9443",
        app_key="app-key",
        app_secret="app-secret",
        transport=httpx2.MockTransport(handler),
    )
    try:
        first = provider.get_flow("005930")
        second = provider.get_flow("005930")
    finally:
        provider.close()

    assert first.foreign_net_quantity == Decimal("1250")
    assert first.foreign_holding_rate == Decimal("51.23")
    assert second.institution_net_quantity == Decimal("-200")
    assert calls == {"token": 1, "flow": 2}


def test_kis_provider_rejects_us_symbols_for_domestic_investor_flow():
    provider = KisInvestorFlowProvider.create(
        base_url="https://example.invalid",
        app_key="app-key",
        app_secret="app-secret",
        transport=httpx2.MockTransport(lambda _: pytest.fail("network call is not expected")),
    )
    try:
        with pytest.raises(ProviderValidationError, match="Korean six-digit"):
            provider.get_flow("AAPL")
    finally:
        provider.close()


def test_kis_provider_maps_daily_flow_and_continuation():
    calls = {"daily": 0}

    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path == "/oauth2/tokenP":
            return httpx2.Response(200, json={"access_token": "token", "expires_in": 3600})
        calls["daily"] += 1
        assert request.headers["tr_id"] == "FHPTJ04160001"
        assert request.url.params["FID_INPUT_DATE_1"] == "20260814"
        if calls["daily"] == 1:
            return httpx2.Response(
                200,
                headers={"tr_cont": "M"},
                json={
                    "rt_cd": "0",
                    "output2": [
                        {
                            "stck_bsop_date": "20260814",
                            "frgn_ntby_qty": "1,000",
                            "orgn_ntby_qty": "-200",
                            "prsn_ntby_qty": "-800",
                        }
                    ],
                },
            )
        assert request.headers["tr_cont"] == "N"
        return httpx2.Response(
            200,
            json={
                "rt_cd": "0",
                "output2": [
                    {
                        "stck_bsop_date": "20260813",
                        "frgn_ntby_qty": "500",
                        "orgn_ntby_qty": "100",
                        "prsn_ntby_qty": "-600",
                    }
                ],
            },
        )

    provider = KisInvestorFlowProvider.create(
        base_url="https://example.test",
        app_key="key",
        app_secret="secret",
        transport=httpx2.MockTransport(handler),
    )
    try:
        rows = provider.get_daily_flows("005930", end_date=date(2026, 8, 14))
    finally:
        provider.close()

    assert [row.trade_date for row in rows] == [date(2026, 8, 13), date(2026, 8, 14)]
    assert rows[-1].foreign_net_quantity == Decimal("1000")
    assert calls["daily"] == 2
