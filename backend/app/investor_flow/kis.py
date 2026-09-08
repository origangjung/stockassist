"""kis 파일은 백엔드 도메인 기능을 담당한다."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx2

from app.investor_flow.contracts import InvestorFlow, InvestorFlowProvider
from app.providers.errors import (
    ProviderAuthenticationError,
    ProviderUnavailableError,
    ProviderValidationError,
)


class KisInvestorFlowProvider(InvestorFlowProvider):
    """KIS domestic-stock investor snapshot adapter.

    KIS exposes this endpoint for Korean listed securities. It is deliberately
    not used for US symbols, whose investor categories are not equivalent.
    """

    name = "kis"

    DAILY_FLOW_PATH = "/uapi/domestic-stock/v1/quotations/investor-trade-by-stock-daily"
    DAILY_FLOW_TR_ID = "FHPTJ04160001"

    def __init__(self, client: httpx2.Client, app_key: str, app_secret: str) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._client = client
        self._app_key = app_key
        self._app_secret = app_secret
        self._token: str | None = None
        self._token_expires_at: datetime | None = None

    @classmethod
    def create(
        cls,
        *,
        base_url: str,
        app_key: str,
        app_secret: str,
        timeout_seconds: float = 15,
        transport: httpx2.BaseTransport | None = None,
    ) -> "KisInvestorFlowProvider":
        """`create`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        return cls(
            httpx2.Client(
                base_url=base_url.rstrip("/"), timeout=timeout_seconds, transport=transport
            ),
            app_key,
            app_secret,
        )

    def get_flow(self, symbol: str) -> InvestorFlow:
        """`get_flow`은(는) 필요한 데이터를 조회해 반환합니다."""

        if not symbol.isdigit() or len(symbol) != 6:
            raise ProviderValidationError(
                "Investor flow is currently supported for Korean six-digit symbols only",
                code="investor-flow-market-not-supported",
            )
        try:
            response = self._client.get(
                "/uapi/domestic-stock/v1/quotations/inquire-investor",
                headers={
                    "authorization": f"Bearer {self._access_token()}",
                    "appkey": self._app_key,
                    "appsecret": self._app_secret,
                    "tr_id": "FHKST01010900",
                    "custtype": "P",
                },
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol},
            )
            response.raise_for_status()
            payload = response.json()
        except httpx2.RequestError as exc:
            raise ProviderUnavailableError(
                "KIS investor-flow API is unavailable", code="kis-unavailable"
            ) from exc
        if not isinstance(payload, dict):
            raise ProviderUnavailableError(
                "KIS returned an invalid response", code="invalid-kis-response"
            )
        if str(payload.get("rt_cd")) != "0":
            message = str(payload.get("msg1") or "KIS investor-flow request failed")
            raise ProviderValidationError(message, code="kis-investor-flow-error")
        output = payload.get("output")
        if not isinstance(output, dict):
            raise ProviderUnavailableError(
                "KIS investor-flow response omitted output", code="invalid-kis-response"
            )
        return InvestorFlow(
            symbol=symbol,
            as_of_date=date.today(),
            foreign_net_quantity=_decimal(output, "frgn_ntby_qty"),
            institution_net_quantity=_decimal(output, "orgn_ntby_qty"),
            individual_net_quantity=_decimal(output, "prsn_ntby_qty"),
            foreign_holding_quantity=_optional_decimal(output, "frgn_hldn_qty"),
            foreign_holding_rate=_optional_decimal(output, "frgn_hldn_rate"),
            data_as_of=datetime.now(timezone.utc),
        )

    def get_daily_flows(
        self,
        symbol: str,
        *,
        end_date: date,
        max_pages: int = 10,
    ) -> list["DailyKisInvestorFlow"]:
        """종목별 과거 투자자 수급을 KIS 연속조회 규칙에 맞춰 가져온다."""

        if not symbol.isdigit() or len(symbol) != 6:
            raise ProviderValidationError(
                "Daily investor flow requires a Korean six-digit symbol",
                code="investor-flow-market-not-supported",
            )
        if not 1 <= max_pages <= 20:
            raise ValueError("max_pages must be between 1 and 20")
        rows: dict[date, DailyKisInvestorFlow] = {}
        continuation = ""
        for _ in range(max_pages):
            payload, continuation = self._daily_flow_page(
                symbol, end_date=end_date, continuation=continuation
            )
            output = payload.get("output2")
            if not isinstance(output, list):
                output = payload.get("output")
            for raw in output if isinstance(output, list) else []:
                parsed = _daily_flow(raw, symbol)
                if parsed is not None and parsed.trade_date <= end_date:
                    rows[parsed.trade_date] = parsed
            if continuation not in {"M", "F"}:
                break
            continuation = "N"
        return [rows[key] for key in sorted(rows)]

    def _daily_flow_page(
        self, symbol: str, *, end_date: date, continuation: str
    ) -> tuple[dict[str, Any], str]:
        """`_daily_flow_page`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        headers = {
            "authorization": f"Bearer {self._access_token()}",
            "appkey": self._app_key,
            "appsecret": self._app_secret,
            "tr_id": self.DAILY_FLOW_TR_ID,
            "custtype": "P",
        }
        if continuation:
            headers["tr_cont"] = continuation
        try:
            response = self._client.get(
                self.DAILY_FLOW_PATH,
                headers=headers,
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": symbol,
                    "FID_INPUT_DATE_1": end_date.strftime("%Y%m%d"),
                    "FID_ORG_ADJ_PRC": "",
                    "FID_ETC_CLS_CODE": "",
                },
            )
            response.raise_for_status()
            payload = response.json()
        except httpx2.HTTPError as exc:
            raise ProviderUnavailableError(
                "KIS daily investor-flow API is unavailable",
                code="kis-daily-flow-unavailable",
            ) from exc
        if not isinstance(payload, dict):
            raise ProviderUnavailableError(
                "KIS returned an invalid daily-flow response",
                code="invalid-kis-response",
            )
        if str(payload.get("rt_cd")) != "0":
            raise ProviderValidationError(
                str(payload.get("msg1") or "KIS daily investor-flow request failed"),
                code="kis-daily-flow-error",
            )
        return payload, response.headers.get("tr_cont", "")

    def _access_token(self) -> str:
        """`_access_token`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        now = datetime.now(timezone.utc)
        if self._token and self._token_expires_at and now < self._token_expires_at:
            return self._token
        try:
            response = self._client.post(
                "/oauth2/tokenP",
                json={
                    "grant_type": "client_credentials",
                    "appkey": self._app_key,
                    "appsecret": self._app_secret,
                },
            )
            response.raise_for_status()
            payload = response.json()
        except httpx2.HTTPError as exc:
            raise ProviderUnavailableError(
                "KIS token service is unavailable", code="kis-auth-unavailable"
            ) from exc
        if not isinstance(payload, dict) or not payload.get("access_token"):
            raise ProviderAuthenticationError(
                "KIS token response is invalid", code="invalid-kis-token"
            )
        self._token = str(payload["access_token"])
        expires_in = int(payload.get("expires_in") or 21_600)
        self._token_expires_at = now + timedelta(seconds=max(60, expires_in - 60))
        return self._token

    def close(self) -> None:
        """`close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        self._client.close()


def _decimal(row: dict[str, Any], field: str) -> Decimal:
    """`_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    value = _optional_decimal(row, field)
    if value is None:
        raise ProviderUnavailableError(f"KIS response omitted {field}", code="invalid-kis-response")
    return value


def _optional_decimal(row: dict[str, Any], field: str) -> Decimal | None:
    """`_optional_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    value = row.get(field)
    if value is None or not str(value).strip():
        return None
    try:
        return Decimal(str(value).replace(",", ""))
    except InvalidOperation as exc:
        raise ProviderUnavailableError(
            f"KIS returned invalid {field}", code="invalid-kis-response"
        ) from exc


@dataclass(frozen=True)
class DailyKisInvestorFlow:
    """KIS 종목별 일별 수급 중 학습에 필요한 시점 정보와 순매수 수량이다."""

    symbol: str
    trade_date: date
    foreign_net_quantity: Decimal
    institution_net_quantity: Decimal
    individual_net_quantity: Decimal


def _daily_flow(row: Any, symbol: str) -> DailyKisInvestorFlow | None:
    """`_daily_flow`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if not isinstance(row, dict):
        return None
    raw_date = row.get("stck_bsop_date") or row.get("bsop_date")
    try:
        trade_date = datetime.strptime(str(raw_date), "%Y%m%d").date()
        return DailyKisInvestorFlow(
            symbol=symbol,
            trade_date=trade_date,
            foreign_net_quantity=_decimal(row, "frgn_ntby_qty"),
            institution_net_quantity=_decimal(row, "orgn_ntby_qty"),
            individual_net_quantity=_decimal(row, "prsn_ntby_qty"),
        )
    except (TypeError, ValueError, ProviderUnavailableError):
        return None
