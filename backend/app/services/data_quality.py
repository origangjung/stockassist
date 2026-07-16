from dataclasses import asdict

from app.repositories.contracts import QualityLogReadRepository


class DataQualityHistoryService:
    def __init__(self, repository: QualityLogReadRepository | None) -> None:
        self._repository = repository

    def recent(
        self,
        *,
        limit: int,
        offset: int,
        symbol: str | None = None,
        severity: str | None = None,
    ) -> dict[str, object]:
        if self._repository is None:
            return {
                "persistence_status": "disabled",
                "items": [],
                "total": 0,
                "severity_counts": {"error": 0, "warning": 0},
                "limit": limit,
                "offset": offset,
            }
        items, total, counts = self._repository.list_recent(
            limit=limit,
            offset=offset,
            symbol=symbol,
            severity=severity,
        )
        return {
            "persistence_status": "enabled",
            "items": [asdict(item) for item in items],
            "total": total,
            "severity_counts": {
                "error": counts.get("error", 0),
                "warning": counts.get("warning", 0),
            },
            "limit": limit,
            "offset": offset,
        }
