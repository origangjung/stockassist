from dataclasses import asdict

from app.providers.audit import ProviderAuditReadRepository


class ProviderAuditHistoryService:
    def __init__(self, repository: ProviderAuditReadRepository | None) -> None:
        self._repository = repository

    def recent(
        self,
        *,
        limit: int,
        offset: int,
        provider: str | None = None,
        outcome: str | None = None,
    ) -> dict[str, object]:
        if self._repository is None:
            return {
                "persistence_status": "disabled",
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
            }
        items, total = self._repository.list_recent(
            limit=limit,
            offset=offset,
            provider=provider,
            outcome=outcome,
        )
        return {
            "persistence_status": "enabled",
            "items": [asdict(item) for item in items],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
