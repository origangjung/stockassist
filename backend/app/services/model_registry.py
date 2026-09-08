"""model_registry 파일은 애플리케이션 사용 사례 기능을 담당한다."""

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
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

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
        """`versions`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
        """`promote`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
        """`_required_repository`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        if self._repository is None:
            raise ModelRegistryUnavailableError("Model registry persistence is disabled")
        return self._repository


class ModelRegistryUnavailableError(RuntimeError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    pass


class ModelVersionNotFoundError(LookupError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    pass


__all__ = [
    "ModelArtifactValidationError",
    "ModelRegistryService",
    "ModelRegistryUnavailableError",
    "ModelVersionNotFoundError",
]
