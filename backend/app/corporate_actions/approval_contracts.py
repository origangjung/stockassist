from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.corporate_actions.contracts import CorporateActionRecord


class CorporateActionApprovalUnavailableError(RuntimeError):
    pass


class CorporateActionApprovalConflictError(ValueError):
    pass


@dataclass(frozen=True)
class CorporateActionApprovalEvidence:
    group_hint: str
    receipt_no: str
    filing_evidence_url: str
    exchange_evidence_url: str
    reviewed_by: str
    reviewed_at: datetime


@dataclass(frozen=True)
class CorporateActionApprovalResult:
    action: CorporateActionRecord
    evidence_hash: str
    created: bool


class CorporateActionApprovalRepository(Protocol):
    def approve(
        self,
        action: CorporateActionRecord,
        evidence: CorporateActionApprovalEvidence,
    ) -> CorporateActionApprovalResult: ...
