"""data_quality 파일은 애플리케이션 사용 사례 기능을 담당한다."""

from dataclasses import asdict

from app.repositories.contracts import QualityLogReadRepository


class DataQualityHistoryService:
    """사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다."""

    def __init__(self, repository: QualityLogReadRepository | None) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._repository = repository

    def recent(
        self,
        *,
        limit: int,
        offset: int,
        symbol: str | None = None,
        severity: str | None = None,
    ) -> dict[str, object]:
        """`recent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
