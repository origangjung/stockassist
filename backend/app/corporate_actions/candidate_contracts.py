"""candidate_contracts 파일은 백엔드 도메인 기능을 담당한다."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol

from app.corporate_actions.contracts import CorporateActionSourceMetadata


@dataclass(frozen=True)
class CorporateActionCandidate:
    """`CorporateActionCandidate` 관련 상태와 동작을 하나의 객체로 묶습니다."""

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
    """계산 또는 처리 결과를 묶어 전달하는 값 객체입니다."""

    source: str
    symbol: str
    fetched_at: datetime
    candidates: tuple[CorporateActionCandidate, ...]


class CorporateActionCandidateProvider(Protocol):
    """`CorporateActionCandidateProvider` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

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
