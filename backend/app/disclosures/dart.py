from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx2

from app.disclosures.contracts import Disclosure, DisclosureProvider
from app.financials.dart import DartFinancialProvider, _raise_dart_error
from app.providers.errors import ProviderUnavailableError


class DartDisclosureProvider(DisclosureProvider):
    """DART disclosure-search provider backed by the official list.json endpoint."""

    name = "dart"

    def __init__(self, dart: DartFinancialProvider) -> None:
        self._dart = dart

    @classmethod
    def create(
        cls,
        *,
        base_url: str,
        api_key: str,
        timeout_seconds: float = 15,
        transport: httpx2.BaseTransport | None = None,
    ) -> "DartDisclosureProvider":
        return cls(
            DartFinancialProvider.create(
                base_url=base_url,
                api_key=api_key,
                timeout_seconds=timeout_seconds,
                transport=transport,
            )
        )

    def list_disclosures(self, symbol: str, *, days: int, limit: int) -> list[Disclosure]:
        today = date.today()
        payload = self._dart.get_json(
            "list.json",
            {
                "corp_code": self._dart.corp_code_for(symbol),
                "bgn_de": (today - timedelta(days=days)).strftime("%Y%m%d"),
                "end_de": today.strftime("%Y%m%d"),
                "last_reprt_at": "Y",
                "page_no": "1",
                "page_count": str(limit),
            },
        )
        status = str(payload.get("status") or "")
        if status == "013":
            return []
        if status != "000":
            _raise_dart_error(payload)
        rows = payload.get("list")
        if not isinstance(rows, list):
            raise ProviderUnavailableError(
                "DART disclosure response omitted rows", code="invalid-dart-response"
            )
        return [_disclosure_from_row(symbol, row) for row in rows if isinstance(row, dict)]

    def close(self) -> None:
        self._dart.close()


def _disclosure_from_row(symbol: str, row: dict[str, Any]) -> Disclosure:
    receipt_no = str(row.get("rcept_no") or "")
    filed_on = str(row.get("rcept_dt") or "")
    try:
        filed_at = datetime.strptime(filed_on, "%Y%m%d").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ProviderUnavailableError(
            "DART returned an invalid disclosure date", code="invalid-dart-response"
        ) from exc
    return Disclosure(
        symbol=symbol,
        corp_code=str(row.get("corp_code") or ""),
        receipt_no=receipt_no,
        company_name=str(row.get("corp_name") or ""),
        report_name=str(row.get("report_nm") or ""),
        filed_at=filed_at,
        filer_name=str(row.get("flr_nm") or ""),
        remarks=str(row["rm"]) if row.get("rm") else None,
        document_url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt_no}",
    )
