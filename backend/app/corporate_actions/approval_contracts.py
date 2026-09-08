"""approval_contracts 파일은 백엔드 도메인 기능을 담당한다."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.corporate_actions.contracts import CorporateActionRecord


class CorporateActionApprovalUnavailableError(RuntimeError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    pass


class CorporateActionApprovalConflictError(ValueError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    pass


@dataclass(frozen=True)
class CorporateActionApprovalEvidence:
    """`CorporateActionApprovalEvidence` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    group_hint: str
    receipt_no: str
    filing_evidence_url: str
    exchange_evidence_url: str
    reviewed_by: str
    reviewed_at: datetime


@dataclass(frozen=True)
class CorporateActionApprovalResult:
    """계산 또는 처리 결과를 묶어 전달하는 값 객체입니다."""

    action: CorporateActionRecord
    evidence_hash: str
    created: bool


class CorporateActionApprovalRepository(Protocol):
    """`CorporateActionApprovalRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    def approve(
        self,
        action: CorporateActionRecord,
        evidence: CorporateActionApprovalEvidence,
    ) -> CorporateActionApprovalResult: ...
