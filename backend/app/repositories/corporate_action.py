from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.corporate_actions import (
    ACTION_STATUSES,
    ACTION_TYPES,
    CorporateActionRecord,
    CorporateActionRevisionConflictError,
)
from app.models.corporate_action import CorporateActionModel


class SqlAlchemyCorporateActionRepository:
    """Persist immutable source-event revisions for point-in-time reconstruction."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def save(self, action: CorporateActionRecord) -> None:
        self._validate(action)
        with self._sessions.begin() as session:
            existing = session.scalar(
                select(CorporateActionModel).where(
                    CorporateActionModel.source == action.source,
                    CorporateActionModel.symbol == action.symbol,
                    CorporateActionModel.event_id == action.event_id,
                    CorporateActionModel.revision == action.revision,
                )
            )
            if existing is not None:
                if self._same_revision(existing, action):
                    return
                raise CorporateActionRevisionConflictError(
                    "Corporate action revision already exists with different values"
                )
            session.add(
                CorporateActionModel(
                    symbol=action.symbol,
                    action_type=action.action_type,
                    event_id=action.event_id,
                    revision=action.revision,
                    effective_at=action.effective_at,
                    announced_at=action.announced_at,
                    known_at=action.known_at,
                    price_factor=action.price_factor,
                    volume_factor=action.volume_factor,
                    status=action.status,
                    source=action.source,
                    rule_version=action.rule_version,
                )
            )

    def list_known(self, symbol: str, *, as_of: datetime) -> list[CorporateActionRecord]:
        self._require_aware(as_of)
        with self._sessions() as session:
            models = session.scalars(
                select(CorporateActionModel)
                .where(
                    CorporateActionModel.symbol == symbol,
                    CorporateActionModel.known_at <= as_of,
                )
                .order_by(
                    CorporateActionModel.effective_at,
                    CorporateActionModel.source,
                    CorporateActionModel.event_id,
                    CorporateActionModel.revision,
                )
            ).all()
            return [self._record(model) for model in models]

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        symbol: str | None = None,
        as_of: datetime | None = None,
    ) -> tuple[list[CorporateActionRecord], int]:
        filters = []
        if symbol is not None:
            filters.append(CorporateActionModel.symbol == symbol)
        if as_of is not None:
            self._require_aware(as_of)
            filters.append(CorporateActionModel.known_at <= as_of)
        with self._sessions() as session:
            total = session.scalar(
                select(func.count()).select_from(CorporateActionModel).where(*filters)
            ) or 0
            models = session.scalars(
                select(CorporateActionModel)
                .where(*filters)
                .order_by(
                    CorporateActionModel.known_at.desc(),
                    CorporateActionModel.id.desc(),
                )
                .offset(offset)
                .limit(limit)
            ).all()
            return [self._record(model) for model in models], total

    @staticmethod
    def _record(model: CorporateActionModel) -> CorporateActionRecord:
        return CorporateActionRecord(
            symbol=model.symbol,
            action_type=model.action_type,
            event_id=model.event_id,
            revision=model.revision,
            effective_at=SqlAlchemyCorporateActionRepository._aware(model.effective_at),
            announced_at=(
                SqlAlchemyCorporateActionRepository._aware(model.announced_at)
                if model.announced_at is not None
                else None
            ),
            known_at=SqlAlchemyCorporateActionRepository._aware(model.known_at),
            price_factor=Decimal(model.price_factor),
            volume_factor=Decimal(model.volume_factor),
            status=model.status,
            source=model.source,
            rule_version=model.rule_version,
            recorded_at=SqlAlchemyCorporateActionRepository._aware(model.created_at),
        )

    @staticmethod
    def _same_revision(model: CorporateActionModel, action: CorporateActionRecord) -> bool:
        return (
            model.symbol == action.symbol
            and model.action_type == action.action_type
            and SqlAlchemyCorporateActionRepository._aware(model.effective_at)
            == action.effective_at
            and (
                SqlAlchemyCorporateActionRepository._aware(model.announced_at)
                if model.announced_at is not None
                else None
            )
            == action.announced_at
            and SqlAlchemyCorporateActionRepository._aware(model.known_at) == action.known_at
            and Decimal(model.price_factor) == action.price_factor
            and Decimal(model.volume_factor) == action.volume_factor
            and model.status == action.status
            and model.rule_version == action.rule_version
        )

    @staticmethod
    def _validate(action: CorporateActionRecord) -> None:
        SqlAlchemyCorporateActionRepository._require_aware(action.effective_at)
        SqlAlchemyCorporateActionRepository._require_aware(action.known_at)
        if action.announced_at is not None:
            SqlAlchemyCorporateActionRepository._require_aware(action.announced_at)
        if action.action_type not in ACTION_TYPES or action.status not in ACTION_STATUSES:
            raise ValueError("Unsupported corporate action classification")
        if action.revision < 1 or action.price_factor <= 0 or action.volume_factor <= 0:
            raise ValueError("Invalid corporate action revision or factors")

    @staticmethod
    def _require_aware(value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Corporate action timestamps must be timezone-aware")

    @staticmethod
    def _aware(value: datetime) -> datetime:
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
