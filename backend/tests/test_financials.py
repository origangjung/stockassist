from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO
from zipfile import ZipFile

import httpx2

from app.financials.dart import DartFinancialProvider
from app.financials.providers import MockFinancialProvider
from app.financials.valuation import (
    ValuationAnalysisService,
    ValuationInputs,
    calculate_valuation_ratios,
)
from app.providers.mock import MockProvider
from app.repositories.memory import InMemoryFinancialRepository
from app.services.financial import FinancialAnalysisService


def test_mock_financials_are_saved_without_substituting_missing_values():
    repository = InMemoryFinancialRepository()
    service = FinancialAnalysisService(MockFinancialProvider(), repository)

    result = service.snapshot("005930", 2025)

    assert result["provider"] == "mock"
    assert result["persistence_status"] == "saved"
    assert result["revenue"] > 0
    assert len(repository.items) == 1


def test_dart_provider_resolves_corp_code_and_normalizes_accounts():
    archive = BytesIO()
    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr(
            "CORPCODE.xml",
            "<result><list><corp_code>00126380</corp_code><corp_name>삼성전자</corp_name><stock_code>005930</stock_code></list></result>",
        )

    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.params["crtfc_key"] == "dart-key"
        if request.url.path == "/api/corpCode.xml":
            return httpx2.Response(200, content=archive.getvalue())
        assert request.url.path == "/api/fnlttSinglAcntAll.json"
        assert request.url.params["corp_code"] == "00126380"
        assert request.url.params["fs_div"] == "CFS"
        return httpx2.Response(
            200,
            json={
                "status": "000",
                "list": [
                    {
                        "account_id": "ifrs-full_Revenue",
                        "account_nm": "매출액",
                        "thstrm_amount": "258,935",
                        "currency": "KRW",
                    },
                    {
                        "account_id": "ifrs-full_OperatingIncomeLoss",
                        "account_nm": "영업이익",
                        "thstrm_amount": "32,726",
                        "currency": "KRW",
                    },
                    {
                        "account_id": "ifrs-full_ProfitLoss",
                        "account_nm": "당기순이익",
                        "thstrm_amount": "34,451",
                        "currency": "KRW",
                    },
                    {
                        "account_id": "ifrs-full_Assets",
                        "account_nm": "자산총계",
                        "thstrm_amount": "514,532",
                        "currency": "KRW",
                    },
                    {
                        "account_id": "ifrs-full_Liabilities",
                        "account_nm": "부채총계",
                        "thstrm_amount": "93,030",
                        "currency": "KRW",
                    },
                    {
                        "account_id": "ifrs-full_Equity",
                        "account_nm": "자본총계",
                        "thstrm_amount": "421,502",
                        "currency": "KRW",
                    },
                ],
            },
        )

    provider = DartFinancialProvider.create(
        base_url="https://opendart.fss.or.kr/api",
        api_key="dart-key",
        transport=httpx2.MockTransport(handler),
    )
    try:
        snapshot = provider.get_snapshot("005930", 2025)
    finally:
        provider.close()

    assert snapshot.corp_code == "00126380"
    assert str(snapshot.revenue) == "258935"
    assert str(snapshot.total_equity) == "421502"


def test_valuation_ratios_fail_closed_for_non_positive_denominators():
    ratios = calculate_valuation_ratios(
        price=Decimal("100"),
        inputs=ValuationInputs(
            revenue=Decimal("1000"),
            net_income=Decimal("-10"),
            equity=Decimal("0"),
            shares_outstanding=Decimal("10"),
            financial_data_as_of=datetime.now(timezone.utc),
            source="test",
        ),
    )
    assert ratios["market_cap"] == Decimal("1000")
    assert ratios["per"] is None
    assert ratios["pbr"] is None
    assert ratios["psr"] == Decimal("1")
    assert ratios["roe"] is None


def test_mock_valuation_uses_quote_and_reported_shares():
    market = MockProvider()
    service = ValuationAnalysisService(
        MockFinancialProvider(), lambda symbol: (market.get_quote(symbol), market.name)
    )
    result = service.analyze("005930", 2025)
    assert result["per"] is not None
    assert result["pbr"] is not None
    assert result["psr"] is not None
    assert result["roe"] is not None
    assert result["experimental"] is True
