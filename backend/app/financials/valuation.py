"""valuation 파일은 백엔드 도메인 기능을 담당한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Callable

from app.financials.contracts import FinancialProvider
from app.local_ai.sec import SecCompanyFactsClient
from app.providers.contracts import Quote


@dataclass(frozen=True)
class ValuationInputs:
    """`ValuationInputs` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    revenue: Decimal | None
    net_income: Decimal | None
    equity: Decimal | None
    shares_outstanding: Decimal | None
    financial_data_as_of: date | datetime
    source: str


def calculate_valuation_ratios(
    *, price: Decimal, inputs: ValuationInputs
) -> dict[str, Decimal | None]:
    """`calculate_valuation_ratios`은(는) 입력 데이터를 기준으로 모델 또는 규칙의 결과 값을 계산해 반환합니다."""

    shares = inputs.shares_outstanding
    market_cap = price * shares if shares is not None and shares > 0 else None
    return {
        "market_cap": market_cap,
        "per": _positive_denominator_ratio(market_cap, inputs.net_income),
        "pbr": _positive_denominator_ratio(market_cap, inputs.equity),
        "psr": _positive_denominator_ratio(market_cap, inputs.revenue),
        "roe": _positive_denominator_ratio(inputs.net_income, inputs.equity),
    }


class ValuationAnalysisService:
    """사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다."""

    def __init__(
        self,
        financial_provider: FinancialProvider,
        quote_loader: Callable[[str], tuple[Quote, str]],
        sec_client: SecCompanyFactsClient | None = None,
    ) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._financial_provider = financial_provider
        self._quote_loader = quote_loader
        self._sec_client = sec_client

    def analyze(
        self, symbol: str, fiscal_year: int, report_code: str = "11011"
    ) -> dict:
        """`analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다."""

        quote, quote_provider = self._quote_loader(symbol)
        if symbol.isdigit():
            snapshot = self._financial_provider.get_snapshot(symbol, fiscal_year, report_code)
            inputs = ValuationInputs(
                revenue=snapshot.revenue,
                net_income=snapshot.net_income,
                equity=snapshot.total_equity,
                shares_outstanding=self._financial_provider.get_issued_shares(
                    symbol, fiscal_year, report_code
                ),
                financial_data_as_of=snapshot.data_as_of,
                source=self._financial_provider.name,
            )
        else:
            if self._sec_client is None:
                inputs = ValuationInputs(
                    revenue=None,
                    net_income=None,
                    equity=None,
                    shares_outstanding=None,
                    financial_data_as_of=datetime.now(timezone.utc),
                    source="sec_unavailable",
                )
            else:
                values = self._sec_client.latest_annual_valuation_inputs(symbol)
                inputs = ValuationInputs(
                    revenue=_decimal(values.get("revenue")),
                    net_income=_decimal(values.get("net_income")),
                    equity=_decimal(values.get("equity")),
                    shares_outstanding=_decimal(values.get("shares_outstanding")),
                    financial_data_as_of=date.fromisoformat(str(values["filed"])),
                    source="sec_companyfacts",
                )
        ratios = calculate_valuation_ratios(price=quote.price, inputs=inputs)
        unavailable = [key for key in ("per", "pbr", "psr", "roe") if ratios[key] is None]
        return {
            "symbol": symbol,
            "currency": quote.currency,
            "price": quote.price,
            "shares_outstanding": inputs.shares_outstanding,
            **ratios,
            "financial_data_as_of": inputs.financial_data_as_of,
            "quote_data_as_of": quote.as_of,
            "financial_source": inputs.source,
            "quote_provider": quote_provider,
            "unavailable_metrics": unavailable,
            "methodology": "point_in_time_market_cap_over_latest_public_annual_fundamentals",
            "experimental": True,
        }


def _positive_denominator_ratio(
    numerator: Decimal | None, denominator: Decimal | None
) -> Decimal | None:
    """`_positive_denominator_ratio`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def _decimal(value: object) -> Decimal | None:
    """`_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if value is None:
        return None
    return Decimal(str(value))
