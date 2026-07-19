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
        self._sessions = sessions

    def count_before(self, cutoffs: dict[str, datetime]) -> dict[str, int]:
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
        unknown = set(cutoffs) - set(_DATASETS)
        if unknown:
            raise ValueError(f"Unsupported lifecycle datasets: {sorted(unknown)}")
