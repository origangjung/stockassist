from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx2

from app.corporate_actions.candidate_contracts import (
    CorporateActionCandidate,
    CorporateActionCandidateFetchResult,
)
from app.corporate_actions.sources import DART_SOURCE
from app.financials.dart import DartFinancialProvider, _raise_dart_error
from app.providers.errors import ProviderUnavailableError


class DartCorporateActionCandidateProvider:
    """Read-only DART collector; candidates cannot enter the adjustment engine directly."""

    metadata = DART_SOURCE

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
    ) -> "DartCorporateActionCandidateProvider":
        return cls(
            DartFinancialProvider.create(
                base_url=base_url,
                api_key=api_key,
                timeout_seconds=timeout_seconds,
                transport=transport,
            )
        )

    def fetch_candidates(
        self,
        symbol: str,
        *,
        start: date,
        end: date,
        limit: int,
    ) -> CorporateActionCandidateFetchResult:
        corp_code = self._dart.corp_code_for(symbol)
        params = {
            "corp_code": corp_code,
            "bgn_de": start.strftime("%Y%m%d"),
            "end_de": end.strftime("%Y%m%d"),
        }
        disclosure_metadata = self._disclosure_metadata(corp_code, start, end, limit)
        candidates = [
            *self._rows(
                "fricDecsn.json",
                params,
                symbol,
                "bonus_issue",
                disclosure_metadata,
            ),
            *self._rows(
                "crDecsn.json",
                params,
                symbol,
                "capital_reduction",
                disclosure_metadata,
            ),
        ]
        candidates.sort(key=lambda item: (item.filed_on, item.event_id), reverse=True)
        if len(candidates) > limit:
            raise ProviderUnavailableError(
                "DART corporate action candidates exceeded the requested limit",
                code="dart-corporate-action-limit-exceeded",
            )
        return CorporateActionCandidateFetchResult(
            source=self.metadata.name,
            symbol=symbol,
            fetched_at=datetime.now(UTC),
            candidates=tuple(candidates),
        )

    def _rows(
        self,
        path: str,
        params: dict[str, str],
        symbol: str,
        candidate_kind: str,
        disclosure_metadata: dict[str, tuple[str | None, str | None]],
    ) -> list[CorporateActionCandidate]:
        payload = self._dart.get_json(path, params)
        status = str(payload.get("status") or "")
        if status == "013":
            return []
        if status != "000":
            _raise_dart_error(payload)
        rows = payload.get("list")
        if not isinstance(rows, list):
            raise ProviderUnavailableError(
                "DART corporate action response omitted rows",
                code="invalid-dart-response",
            )
        return [
            self._candidate(
                symbol,
                row,
                candidate_kind,
                disclosure_metadata.get(str(row.get("rcept_no") or ""), (None, None)),
            )
            for row in rows
            if isinstance(row, dict)
        ]

    @staticmethod
    def _candidate(
        symbol: str,
        row: dict[str, Any],
        candidate_kind: str,
        disclosure_metadata: tuple[str | None, str | None],
    ) -> CorporateActionCandidate:
        receipt_no = str(row.get("rcept_no") or "").strip()
        if len(receipt_no) != 14 or not receipt_no.isdigit():
            raise ProviderUnavailableError(
                "DART returned an invalid corporate action receipt number",
                code="invalid-dart-response",
            )
        filed_on = _date(receipt_no[:8], required=True)
        common_warnings = [
            "revision_reconciliation_required",
            "exchange_effective_date_required",
        ]
        report_name, remarks = disclosure_metadata
        correction_hint = bool(report_name and "정정" in report_name)
        superseded_hint = bool(remarks and "정" in remarks)
        if correction_hint:
            common_warnings.append("correction_title_requires_reconciliation")
        if superseded_hint:
            common_warnings.append("later_correction_reported")
        if remarks and "철" in remarks:
            common_warnings.append("withdrawal_report_reference_required")
        if candidate_kind == "bonus_issue":
            ratio = _decimal(row.get("fric_nstk_ascnt_ps_ostk"))
            if ratio is None or ratio <= 0:
                price_factor = volume_factor = None
                common_warnings.append("invalid_common_share_allocation_ratio")
            else:
                volume_factor = Decimal(1) + ratio
                price_factor = Decimal(1) / volume_factor
            action_type = "stock_dividend"
            decision_date = _date(row.get("fric_bddd"))
            record_date = _date(row.get("fric_nstk_asstd"))
        else:
            before = _decimal(row.get("bfcr_tisstk_ostk"))
            after = _decimal(row.get("atcr_tisstk_ostk"))
            if before is None or after is None or before <= 0 or not 0 < after < before:
                price_factor = volume_factor = None
                common_warnings.append("invalid_outstanding_share_reduction")
            else:
                price_factor = before / after
                volume_factor = after / before
            common_warnings.append("proportional_consolidation_evidence_required")
            action_type = "reverse_split"
            decision_date = _date(row.get("bddd"))
            record_date = _date(row.get("cr_std"))
        return CorporateActionCandidate(
            source=DART_SOURCE.name,
            symbol=symbol,
            event_id=f"dart:{receipt_no}:{candidate_kind}",
            receipt_no=receipt_no,
            action_type=action_type,
            filed_on=filed_on,
            decision_date=decision_date,
            record_date=record_date,
            proposed_price_factor=price_factor,
            proposed_volume_factor=volume_factor,
            evidence_url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt_no}",
            report_name=report_name,
            remarks=remarks,
            correction_hint=correction_hint,
            superseded_hint=superseded_hint,
            warnings=tuple(common_warnings),
        )

    def _disclosure_metadata(
        self,
        corp_code: str,
        start: date,
        end: date,
        limit: int,
    ) -> dict[str, tuple[str | None, str | None]]:
        base_params = {
            "corp_code": corp_code,
            "bgn_de": start.strftime("%Y%m%d"),
            "end_de": end.strftime("%Y%m%d"),
            "last_reprt_at": "N",
            "pblntf_ty": "B",
            "sort": "date",
            "sort_mth": "asc",
            "page_count": "100",
        }
        metadata: dict[str, tuple[str | None, str | None]] = {}
        maximum_pages = min(2, (limit + 99) // 100)
        for page_no in range(1, maximum_pages + 1):
            payload = self._dart.get_json(
                "list.json", {**base_params, "page_no": str(page_no)}
            )
            status = str(payload.get("status") or "")
            if status == "013":
                break
            if status != "000":
                _raise_dart_error(payload)
            rows = payload.get("list")
            if not isinstance(rows, list):
                raise ProviderUnavailableError(
                    "DART disclosure metadata response omitted rows",
                    code="invalid-dart-response",
                )
            for row in rows:
                if not isinstance(row, dict):
                    continue
                receipt_no = str(row.get("rcept_no") or "").strip()
                if receipt_no:
                    metadata[receipt_no] = (
                        str(row["report_nm"]) if row.get("report_nm") else None,
                        str(row["rm"]) if row.get("rm") else None,
                    )
            try:
                total_pages = int(payload.get("total_page") or 1)
            except (TypeError, ValueError) as exc:
                raise ProviderUnavailableError(
                    "DART disclosure metadata returned invalid pagination",
                    code="invalid-dart-response",
                ) from exc
            if page_no >= total_pages:
                break
        return metadata

    def close(self) -> None:
        self._dart.close()


def _date(value: object, *, required: bool = False) -> date | None:
    raw = str(value or "").strip().replace("-", "").replace(".", "")
    if not raw and not required:
        return None
    try:
        return datetime.strptime(raw, "%Y%m%d").date()
    except ValueError as exc:
        raise ProviderUnavailableError(
            "DART returned an invalid corporate action date",
            code="invalid-dart-response",
        ) from exc


def _decimal(value: object) -> Decimal | None:
    raw = str(value or "").strip().replace(",", "")
    if not raw or raw == "-":
        return None
    try:
        parsed = Decimal(raw)
    except InvalidOperation:
        return None
    return parsed if parsed.is_finite() else None
