"""provider_audit 파일은 데이터 저장과 조회 기능을 담당한다."""

from dataclasses import asdict

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.models.provider_audit import ProviderAuditLogModel
from app.providers.audit import ProviderAuditEvent, ProviderAuditRecord


class SqlAlchemyProviderAuditRepository:
    """도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._sessions = sessions

    def save(self, event: ProviderAuditEvent) -> None:
        """`save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
        """`list_recent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
        """`delete_before`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다."""

        with self._sessions.begin() as session:
            result = session.execute(
                delete(ProviderAuditLogModel).where(ProviderAuditLogModel.occurred_at < cutoff)
            )
            return max(result.rowcount or 0, 0)
