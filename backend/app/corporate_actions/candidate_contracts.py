from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol

from app.corporate_actions.contracts import CorporateActionSourceMetadata


@dataclass(frozen=True)
class CorporateActionCandidate:
    source: str
    symbol: str
    event_id: str
    receipt_no: str
    action_type: str
    filed_on: date
    decision_date: date | None
    record_date: date | None
    proposed_price_factor: Decimal | None
    proposed_volume_factor: Decimal | None
    evidence_url: str
    report_name: str | None
    remarks: str | None
    correction_hint: bool
    superseded_hint: bool
    warnings: tuple[str, ...]
    confirmation_ready: bool = False


@dataclass(frozen=True)
class CorporateActionCandidateFetchResult:
    source: str
    symbol: str
    fetched_at: datetime
    candidates: tuple[CorporateActionCandidate, ...]


class CorporateActionCandidateProvider(Protocol):
    metadata: CorporateActionSourceMetadata

    def fetch_candidates(
        self,
        symbol: str,
        *,
        start: date,
        end: date,
        limit: int,
    ) -> CorporateActionCandidateFetchResult: ...

    def close(self) -> None: ...
