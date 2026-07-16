from datetime import datetime, timezone
from decimal import Decimal

from app.config import Settings
from app.financials.contracts import FinancialProvider, FinancialSnapshot


class MockFinancialProvider(FinancialProvider):
    """Deterministic baseline financials for offline development and tests."""

    name = "mock"
    _values = {
        "005930": (
            "00126380",
            "258935494000000",
            "32725996000000",
            "34451400000000",
            "514532000000000",
            "93030000000000",
            "421502000000000",
        ),
        "000660": (
            "00164779",
            "42850000000000",
            "19100000000000",
            "15400000000000",
            "112000000000000",
            "41500000000000",
            "70500000000000",
        ),
        "035420": (
            "00266961",
            "10400000000000",
            "1900000000000",
            "1600000000000",
            "37000000000000",
            "12800000000000",
            "24200000000000",
        ),
    }

    def get_snapshot(
        self, symbol: str, fiscal_year: int, report_code: str = "11011"
    ) -> FinancialSnapshot:
        try:
            corp_code, *amounts = self._values[symbol]
        except KeyError as exc:
            from app.providers.errors import ProviderNotFoundError

            raise ProviderNotFoundError(
                f"Mock financial data does not contain {symbol}", code="financial-not-found"
            ) from exc
        revenue, operating_income, net_income, assets, liabilities, equity = map(Decimal, amounts)
        return FinancialSnapshot(
            symbol=symbol,
            corp_code=corp_code,
            fiscal_year=fiscal_year,
            report_code=report_code,
            statement_type="CFS",
            currency="KRW",
            revenue=revenue,
            operating_income=operating_income,
            net_income=net_income,
            total_assets=assets,
            total_liabilities=liabilities,
            total_equity=equity,
            data_as_of=datetime.now(timezone.utc),
        )


def build_financial_provider(settings: Settings) -> FinancialProvider:
    if settings.financial_provider == "mock":
        return MockFinancialProvider()
    key = settings.dart_api_key.get_secret_value() if settings.dart_api_key else ""
    if not key:
        raise ValueError("DART_API_KEY is required when FINANCIAL_PROVIDER=dart")
    from app.financials.dart import DartFinancialProvider

    return DartFinancialProvider.create(
        base_url=settings.dart_base_url,
        api_key=key,
        timeout_seconds=settings.dart_timeout_seconds,
    )
