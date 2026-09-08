"""data_lifecycle 파일은 데이터 저장과 조회 기능을 담당한다."""

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.models.content import DisclosureModel, NewsArticleModel
from app.models.market import DataQualityLogModel

_DATASETS = {
    "data_quality_logs": (DataQualityLogModel, DataQualityLogModel.created_at),
    "news": (NewsArticleModel, NewsArticleModel.created_at),
    "disclosures": (DisclosureModel, DisclosureModel.created_at),
}


class SqlAlchemyDataLifecycleRepository:
    """Delete only explicitly allowlisted cache and operational history tables."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._sessions = sessions

    def count_before(self, cutoffs: dict[str, datetime]) -> dict[str, int]:
        """`count_before`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        self._validate_datasets(cutoffs)
        with self._sessions() as session:
            return {
                dataset: (
                    session.scalar(
                        select(func.count()).select_from(model).where(column < cutoff)
                    )
                    or 0
                )
                for dataset, cutoff in cutoffs.items()
                for model, column in [_DATASETS[dataset]]
            }

    def delete_before(self, cutoffs: dict[str, datetime]) -> dict[str, int]:
        """`delete_before`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다."""

        self._validate_datasets(cutoffs)
        with self._sessions.begin() as session:
            deleted: dict[str, int] = {}
            for dataset, cutoff in cutoffs.items():
                model, column = _DATASETS[dataset]
                result = session.execute(delete(model).where(column < cutoff))
                deleted[dataset] = max(result.rowcount or 0, 0)
            return deleted

    @staticmethod
    def _validate_datasets(cutoffs: dict[str, datetime]) -> None:
        """`_validate_datasets`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다."""

        unknown = set(cutoffs) - set(_DATASETS)
        if unknown:
            raise ValueError(f"Unsupported lifecycle datasets: {sorted(unknown)}")
