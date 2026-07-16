from dataclasses import asdict

from app.repositories.contracts import PredictionRepository


class ModelRegistryService:
    """Metadata registry for per-symbol experimental prediction models."""

    def __init__(self, repository: PredictionRepository | None) -> None:
        self._repository = repository

    def versions(
        self,
        *,
        limit: int,
        offset: int,
        symbol: str | None = None,
        algorithm: str | None = None,
        horizon_days: int | None = None,
    ) -> dict:
        if self._repository is None:
            return {
                "persistence_status": "disabled",
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
            }
        records, total = self._repository.list_versions(
            limit=limit,
            offset=offset,
            symbol=symbol,
            algorithm=algorithm,
            horizon_days=horizon_days,
        )
        return {
            "persistence_status": "enabled",
            "items": [asdict(record) for record in records],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def promote(self, version: str) -> dict:
        repository = self._required_repository()
        record = repository.promote(version)
        if record is None:
            raise ModelVersionNotFoundError(f"Model version not found: {version}")
        return {
            "model": asdict(record),
            "runtime_activation": False,
            "validation_status": record.validation_status,
            "notice": (
                "Champion promotion updates registry metadata only. Runtime artifact activation "
                "requires a separately validated deployment workflow."
            ),
        }

    def _required_repository(self) -> PredictionRepository:
        if self._repository is None:
            raise ModelRegistryUnavailableError("Model registry persistence is disabled")
        return self._repository


class ModelRegistryUnavailableError(RuntimeError):
    pass


class ModelVersionNotFoundError(LookupError):
    pass
