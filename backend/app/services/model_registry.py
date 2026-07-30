from dataclasses import asdict

from app.repositories.contracts import PredictionRepository
from app.prediction.artifacts import ModelArtifactStore, ModelArtifactValidationError


class ModelRegistryService:
    """Metadata registry for per-symbol experimental prediction models."""

    def __init__(
        self,
        repository: PredictionRepository | None,
        artifact_store: ModelArtifactStore | None = None,
    ) -> None:
        self._repository = repository
        self._artifact_store = artifact_store

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
                "runtime_activation_enabled": self._artifact_store is not None,
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
            "runtime_activation_enabled": self._artifact_store is not None,
            "items": [asdict(record) for record in records],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def promote(self, version: str) -> dict:
        repository = self._required_repository()
        candidate = repository.get_version(version)
        if candidate is None:
            raise ModelVersionNotFoundError(f"Model version not found: {version}")
        if self._artifact_store is not None:
            self._artifact_store.verify(
                version,
                symbol=candidate.symbol,
                algorithm=candidate.algorithm,
                horizon_days=candidate.horizon_days,
            )
        record = repository.promote(version)
        if record is None:
            raise ModelVersionNotFoundError(f"Model version not found: {version}")
        runtime_activation = False
        if self._artifact_store is not None:
            self._artifact_store.activate(
                version,
                symbol=record.symbol,
                algorithm=record.algorithm,
                horizon_days=record.horizon_days,
            )
            runtime_activation = True
        return {
            "model": asdict(record),
            "runtime_activation": runtime_activation,
            "validation_status": record.validation_status,
            "notice": (
                "Champion promotion activated a checksum-verified runtime artifact."
                if runtime_activation
                else "Champion promotion updates registry metadata only. Runtime artifact "
                "activation is disabled until a validated artifact store is configured."
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


__all__ = [
    "ModelArtifactValidationError",
    "ModelRegistryService",
    "ModelRegistryUnavailableError",
    "ModelVersionNotFoundError",
]
