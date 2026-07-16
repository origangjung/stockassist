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

    def __init__(self, client: httpx2.Client, app_key: str, app_secret: str) -> None:
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
        return cls(
            httpx2.Client(
                base_url=base_url.rstrip("/"), timeout=timeout_seconds, transport=transport
            ),
            app_key,
            app_secret,
        )

    def get_flow(self, symbol: str) -> InvestorFlow:
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

    def _access_token(self) -> str:
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
        except httpx2.RequestError as exc:
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
        self._client.close()


def _decimal(row: dict[str, Any], field: str) -> Decimal:
    value = _optional_decimal(row, field)
    if value is None:
        raise ProviderUnavailableError(f"KIS response omitted {field}", code="invalid-kis-response")
    return value


def _optional_decimal(row: dict[str, Any], field: str) -> Decimal | None:
    value = row.get(field)
    if value is None or not str(value).strip():
        return None
    try:
        return Decimal(str(value).replace(",", ""))
    except InvalidOperation as exc:
        raise ProviderUnavailableError(
            f"KIS returned invalid {field}", code="invalid-kis-response"
        ) from exc
