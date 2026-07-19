from dataclasses import asdict

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.models.provider_audit import ProviderAuditLogModel
from app.providers.audit import ProviderAuditEvent, ProviderAuditRecord


class SqlAlchemyProviderAuditRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def save(self, event: ProviderAuditEvent) -> None:
        with self._sessions.begin() as session:
            session.add(ProviderAuditLogModel(**asdict(event)))

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        provider: str | None = None,
        outcome: str | None = None,
    ) -> tuple[list[ProviderAuditRecord], int]:
        filters = []
        if provider:
            filters.append(ProviderAuditLogModel.provider == provider)
        if outcome:
            filters.append(ProviderAuditLogModel.outcome == outcome)
        with self._sessions() as session:
            total = (
                session.scalar(
                    select(func.count()).select_from(ProviderAuditLogModel).where(*filters)
                )
                or 0
            )
            models = session.scalars(
                select(ProviderAuditLogModel)
                .where(*filters)
                .order_by(
                    ProviderAuditLogModel.occurred_at.desc(),
                    ProviderAuditLogModel.id.desc(),
                )
                .offset(offset)
                .limit(limit)
            ).all()
            return (
                [
                    ProviderAuditRecord(
                        audit_id=model.id,
                        provider=model.provider,
                        method=model.method,
                        endpoint=model.endpoint,
                        api_group=model.api_group,
                        outcome=model.outcome,
                        status_code=model.status_code,
                        error_code=model.error_code,
                        provider_request_id=model.provider_request_id,
                        internal_request_id=model.internal_request_id,
                        attempt_count=model.attempt_count,
                        duration_ms=model.duration_ms,
                        occurred_at=model.occurred_at,
                    )
                    for model in models
                ],
                total,
            )

    def delete_before(self, cutoff: datetime) -> int:
        with self._sessions.begin() as session:
            result = session.execute(
                delete(ProviderAuditLogModel).where(ProviderAuditLogModel.occurred_at < cutoff)
            )
            return max(result.rowcount or 0, 0)
