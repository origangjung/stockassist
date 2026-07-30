import json
from dataclasses import replace
from decimal import ROUND_HALF_EVEN, Decimal, DecimalException
from hashlib import sha256

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.corporate_actions.approval_contracts import (
    CorporateActionApprovalConflictError,
    CorporateActionApprovalEvidence,
    CorporateActionApprovalResult,
)
from app.corporate_actions.contracts import ACTION_TYPES, CorporateActionRecord
from app.models.corporate_action import (
    CorporateActionApprovalModel,
    CorporateActionModel,
)
from app.models.market import StockModel
from app.repositories.corporate_action import SqlAlchemyCorporateActionRepository


class SqlAlchemyCorporateActionApprovalRepository:
    """Atomically freeze a reviewed candidate and its immutable evidence."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def approve(
        self,
        action: CorporateActionRecord,
        evidence: CorporateActionApprovalEvidence,
    ) -> CorporateActionApprovalResult:
        action = self._canonical(action)
        self._validate(action, evidence)
        evidence_hash = self._evidence_hash(action, evidence)

        with self._sessions.begin() as session:
            locked_symbol = session.scalar(
                select(StockModel.symbol)
                .where(StockModel.symbol == action.symbol)
                .with_for_update()
            )
            if locked_symbol is None:
                raise CorporateActionApprovalConflictError(
                    "Corporate action symbol is not present in the stock master"
                )
            existing = session.scalar(
                select(CorporateActionApprovalModel).where(
                    CorporateActionApprovalModel.evidence_hash == evidence_hash
                )
            )
            if existing is not None:
                model = session.get(CorporateActionModel, existing.corporate_action_id)
                if model is None:
                    raise RuntimeError("Corporate action approval references a missing action")
                return CorporateActionApprovalResult(
                    action=SqlAlchemyCorporateActionRepository._record(model),
                    evidence_hash=evidence_hash,
                    created=False,
                )

            latest_revision = session.scalar(
                select(func.max(CorporateActionModel.revision)).where(
                    CorporateActionModel.source == action.source,
                    CorporateActionModel.symbol == action.symbol,
                    CorporateActionModel.event_id == action.event_id,
                )
            )
            revision = int(latest_revision or 0) + 1
            model = CorporateActionModel(
                symbol=action.symbol,
                action_type=action.action_type,
                event_id=action.event_id,
                revision=revision,
                effective_at=action.effective_at,
                announced_at=action.announced_at,
                known_at=evidence.reviewed_at,
                price_factor=action.price_factor,
                volume_factor=action.volume_factor,
                status="confirmed",
                source=action.source,
                rule_version=action.rule_version,
            )
            session.add(model)
            session.flush()
            session.add(
                CorporateActionApprovalModel(
                    corporate_action_id=model.id,
                    group_hint=evidence.group_hint,
                    receipt_no=evidence.receipt_no,
                    filing_evidence_url=evidence.filing_evidence_url,
                    exchange_evidence_url=evidence.exchange_evidence_url,
                    reviewed_by=evidence.reviewed_by,
                    reviewed_at=evidence.reviewed_at,
                    evidence_hash=evidence_hash,
                )
            )
            session.flush()
            return CorporateActionApprovalResult(
                action=SqlAlchemyCorporateActionRepository._record(model),
                evidence_hash=evidence_hash,
                created=True,
            )

    @staticmethod
    def _evidence_hash(
        action: CorporateActionRecord,
        evidence: CorporateActionApprovalEvidence,
    ) -> str:
        payload = {
            "source": action.source,
            "symbol": action.symbol,
            "event_id": action.event_id,
            "action_type": action.action_type,
            "effective_at": action.effective_at.isoformat(),
            "announced_at": action.announced_at.isoformat() if action.announced_at else None,
            "price_factor": format(action.price_factor, "f"),
            "volume_factor": format(action.volume_factor, "f"),
            "rule_version": action.rule_version,
            "group_hint": evidence.group_hint,
            "receipt_no": evidence.receipt_no,
            "filing_evidence_url": evidence.filing_evidence_url,
            "exchange_evidence_url": evidence.exchange_evidence_url,
            "reviewed_by": evidence.reviewed_by,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode()).hexdigest()

    @staticmethod
    def _canonical(action: CorporateActionRecord) -> CorporateActionRecord:
        try:
            return replace(
                action,
                price_factor=action.price_factor.quantize(
                    Decimal("0.000000000001"), rounding=ROUND_HALF_EVEN
                ),
                volume_factor=action.volume_factor.quantize(
                    Decimal("0.000000000001"), rounding=ROUND_HALF_EVEN
                ),
            )
        except DecimalException as exc:
            raise ValueError("Corporate action factors exceed persistence precision") from exc

    @staticmethod
    def _validate(
        action: CorporateActionRecord,
        evidence: CorporateActionApprovalEvidence,
    ) -> None:
        timestamps = [action.effective_at, evidence.reviewed_at]
        if action.announced_at is not None:
            timestamps.append(action.announced_at)
        if any(value.tzinfo is None or value.utcoffset() is None for value in timestamps):
            raise ValueError("Corporate action approval timestamps must be timezone-aware")
        if action.action_type not in ACTION_TYPES:
            raise ValueError("Unsupported corporate action classification")
        if action.price_factor <= 0 or action.volume_factor <= 0:
            raise ValueError("Corporate action approval factors must be positive")
        if action.known_at != evidence.reviewed_at:
            raise ValueError("Approved corporate action known_at must equal reviewed_at")
        if not evidence.reviewed_by.strip():
            raise ValueError("Corporate action approval reviewer is required")
