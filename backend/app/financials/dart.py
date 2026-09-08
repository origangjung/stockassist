"""dart 파일은 백엔드 도메인 기능을 담당한다."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import Any
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

import httpx2

from app.financials.contracts import FinancialProvider, FinancialSnapshot
from app.providers.errors import (
    ProviderNotFoundError,
    ProviderUnavailableError,
    ProviderValidationError,
)


_ACCOUNT_IDS = {
    "revenue": {"ifrs-full_Revenue", "dart_Revenue", "ifrs-full_SalesRevenue"},
    "operating_income": {"ifrs-full_OperatingIncomeLoss", "dart_OperatingIncomeLoss"},
    "net_income": {"ifrs-full_ProfitLoss", "dart_ProfitLoss"},
    "total_assets": {"ifrs-full_Assets"},
    "total_liabilities": {"ifrs-full_Liabilities"},
    "total_equity": {"ifrs-full_Equity"},
}
_ACCOUNT_NAMES = {
    "revenue": {"매출액", "영업수익", "수익(매출액)"},
    "operating_income": {"영업이익", "영업손익"},
    "net_income": {"당기순이익", "당기순손익", "분기순이익"},
    "total_assets": {"자산총계"},
    "total_liabilities": {"부채총계"},
    "total_equity": {"자본총계"},
}


class DartFinancialProvider(FinancialProvider):
    """외부 또는 모의 데이터 원천을 동일한 계약으로 제공하는 구현체입니다."""

    name = "dart"

    def __init__(self, client: httpx2.Client, api_key: str) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._client = client
        self._api_key = api_key
        self._corp_codes: dict[str, str] | None = None

    @classmethod
    def create(
        cls,
        *,
        base_url: str,
        api_key: str,
        timeout_seconds: float = 15,
        transport: httpx2.BaseTransport | None = None,
    ) -> "DartFinancialProvider":
        """`create`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        return cls(
            httpx2.Client(
                base_url=f"{base_url.rstrip('/')}/",
                timeout=timeout_seconds,
                transport=transport,
            ),
            api_key,
        )

    def get_snapshot(
        self, symbol: str, fiscal_year: int, report_code: str = "11011"
    ) -> FinancialSnapshot:
        """`get_snapshot`은(는) 필요한 데이터를 조회해 반환합니다."""

        corp_code = self._corp_code_for(symbol)
        payload, statement_type = self._statement_payload(corp_code, fiscal_year, report_code)
        rows = payload.get("list")
        if not isinstance(rows, list):
            raise ProviderUnavailableError(
                "DART financial response omitted account rows", code="invalid-dart-response"
            )
        accounts = _extract_accounts(rows)
        currency = _first_currency(rows)
        return FinancialSnapshot(
            symbol=symbol,
            corp_code=corp_code,
            fiscal_year=fiscal_year,
            report_code=report_code,
            statement_type=statement_type,
            currency=currency,
            revenue=accounts["revenue"],
            operating_income=accounts["operating_income"],
            net_income=accounts["net_income"],
            total_assets=accounts["total_assets"],
            total_liabilities=accounts["total_liabilities"],
            total_equity=accounts["total_equity"],
            data_as_of=datetime.now(timezone.utc),
        )

    def corp_code_for(self, symbol: str) -> str:
        """Resolve an exchange symbol to DART's corporation code."""
        return self._corp_code_for(symbol)

    def get_issued_shares(
        self, symbol: str, fiscal_year: int, report_code: str = "11011"
    ) -> Decimal | None:
        """`get_issued_shares`은(는) 필요한 데이터를 조회해 반환합니다."""

        payload = self._json_get(
            "stockTotqySttus.json",
            {
                "corp_code": self._corp_code_for(symbol),
                "bsns_year": str(fiscal_year),
                "reprt_code": report_code,
            },
        )
        if payload.get("status") != "000":
            if payload.get("status") == "013":
                return None
            _raise_dart_error(payload)
        rows = payload.get("list")
        if not isinstance(rows, list):
            return None
        for row in rows:
            if not isinstance(row, dict):
                continue
            category = str(row.get("se") or row.get("stock_knd") or "")
            if "합계" in category or category.lower() == "total":
                return _amount(row.get("istc_totqy") or row.get("now_to_isu_stock_totqy"))
        return None

    def get_json(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        """Call another DART JSON endpoint with the configured credentials."""
        return self._json_get(path, params)

    def _corp_code_for(self, symbol: str) -> str:
        """`_corp_code_for`은(는) 입력 조건을 지원하는 제공자나 처리 대상을 선택해 반환합니다."""

        if self._corp_codes is None:
            self._corp_codes = self._load_corp_codes()
        try:
            return self._corp_codes[symbol]
        except KeyError as exc:
            raise ProviderNotFoundError(
                f"DART corporation code was not found for {symbol}", code="dart-corp-not-found"
            ) from exc

    def _load_corp_codes(self) -> dict[str, str]:
        """`_load_corp_codes`은(는) 필요한 데이터를 조회해 반환합니다."""

        try:
            response = self._client.get("corpCode.xml", params={"crtfc_key": self._api_key})
            response.raise_for_status()
            archive = ZipFile(BytesIO(response.content))
            xml_name = next(name for name in archive.namelist() if name.lower().endswith(".xml"))
            root = ElementTree.fromstring(archive.read(xml_name))
        except (httpx2.RequestError, BadZipFile, ElementTree.ParseError, StopIteration) as exc:
            raise ProviderUnavailableError(
                "DART corporation-code catalog could not be loaded", code="dart-corp-catalog-error"
            ) from exc
        return {
            stock_code.strip(): corp_code.strip()
            for item in root.findall("list")
            if (stock_code := item.findtext("stock_code"))
            and stock_code.strip()
            and (corp_code := item.findtext("corp_code"))
        }

    def _statement_payload(
        self, corp_code: str, fiscal_year: int, report_code: str
    ) -> tuple[dict[str, Any], str]:
        """`_statement_payload`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        for statement_type in ("CFS", "OFS"):
            payload = self._json_get(
                "fnlttSinglAcntAll.json",
                {
                    "corp_code": corp_code,
                    "bsns_year": str(fiscal_year),
                    "reprt_code": report_code,
                    "fs_div": statement_type,
                },
            )
            if payload.get("status") == "000":
                return payload, statement_type
            if payload.get("status") != "013":
                _raise_dart_error(payload)
        raise ProviderNotFoundError(
            "DART does not have this company's financial statement for the requested period",
            code="dart-financial-not-found",
        )

    def _json_get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        """`_json_get`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        try:
            response = self._client.get(path, params={"crtfc_key": self._api_key, **params})
            response.raise_for_status()
            payload = response.json()
        except (httpx2.RequestError, ValueError) as exc:
            raise ProviderUnavailableError(
                "DART API is unavailable", code="dart-unavailable"
            ) from exc
        if not isinstance(payload, dict):
            raise ProviderUnavailableError(
                "DART returned an invalid response", code="invalid-dart-response"
            )
        return payload

    def close(self) -> None:
        """`close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        self._client.close()


def _extract_accounts(rows: list[Any]) -> dict[str, Decimal | None]:
    """`_extract_accounts`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    values: dict[str, Decimal | None] = {key: None for key in _ACCOUNT_IDS}
    for row in rows:
        if not isinstance(row, dict):
            continue
        account_id = str(row.get("account_id") or "")
        account_name = str(row.get("account_nm") or "")
        for metric, identifiers in _ACCOUNT_IDS.items():
            if values[metric] is None and (
                account_id in identifiers or account_name in _ACCOUNT_NAMES[metric]
            ):
                values[metric] = _amount(row.get("thstrm_amount"))
    return values


def _amount(value: Any) -> Decimal | None:
    """`_amount`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if value is None or not str(value).strip() or str(value).strip() == "-":
        return None
    normalized = str(value).strip().replace(",", "")
    if normalized.startswith("(") and normalized.endswith(")"):
        normalized = f"-{normalized[1:-1]}"
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise ProviderUnavailableError(
            "DART returned an invalid account amount", code="invalid-dart-response"
        ) from exc


def _first_currency(rows: list[Any]) -> str:
    """`_first_currency`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    for row in rows:
        if isinstance(row, dict) and row.get("currency"):
            return str(row["currency"])
    return "KRW"


def _raise_dart_error(payload: dict[str, Any]) -> None:
    """`_raise_dart_error`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    code = str(payload.get("status") or "dart-error")
    message = str(payload.get("message") or "DART API request failed")
    if code in {"010", "011", "012", "020", "021", "100", "101", "800", "900", "901"}:
        raise ProviderValidationError(message, code=f"dart-{code}")
    raise ProviderUnavailableError(message, code=f"dart-{code}")
