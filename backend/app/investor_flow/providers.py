from datetime import datetime, timezone
from decimal import Decimal

from app.config import Settings
from app.investor_flow.contracts import InvestorFlow, InvestorFlowProvider
from app.providers.errors import ProviderNotFoundError


class MockInvestorFlowProvider(InvestorFlowProvider):
    name = "mock"
    _flows = {
        "005930": ("1580000", "-420000", "-1160000", "3020000000", "51.12"),
        "000660": ("740000", "390000", "-1130000", "578000000", "54.72"),
        "035420": ("-125000", "-68000", "193000", "226000000", "47.80"),
    }

    def get_flow(self, symbol: str) -> InvestorFlow:
        try:
            values = self._flows[symbol]
        except KeyError as exc:
            raise ProviderNotFoundError(
                f"Mock investor-flow data does not contain {symbol}", code="investor-flow-not-found"
            ) from exc
        foreign, institution, individual, holding, rate = map(Decimal, values)
        now = datetime.now(timezone.utc)
        return InvestorFlow(
            symbol=symbol,
            as_of_date=now.date(),
            foreign_net_quantity=foreign,
            institution_net_quantity=institution,
            individual_net_quantity=individual,
            foreign_holding_quantity=holding,
            foreign_holding_rate=rate,
            data_as_of=now,
        )


def build_investor_flow_provider(settings: Settings) -> InvestorFlowProvider:
    if settings.investor_flow_provider == "mock":
        return MockInvestorFlowProvider()
    app_key = settings.kis_app_key.get_secret_value() if settings.kis_app_key else ""
    app_secret = settings.kis_app_secret.get_secret_value() if settings.kis_app_secret else ""
    if not app_key or not app_secret:
        raise ValueError(
            "KIS_APP_KEY and KIS_APP_SECRET are required when INVESTOR_FLOW_PROVIDER=kis"
        )
    from app.investor_flow.kis import KisInvestorFlowProvider

    return KisInvestorFlowProvider.create(
        base_url=settings.kis_base_url,
        app_key=app_key,
        app_secret=app_secret,
        timeout_seconds=settings.kis_timeout_seconds,
    )
