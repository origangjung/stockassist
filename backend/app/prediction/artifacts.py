from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from threading import RLock
from uuid import uuid4


_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_SYMBOL_PATTERN = re.compile(r"^[0-9A-Z.-]{1,16}$")
_MAX_MANIFEST_BYTES = 64 * 1024
_MAX_ARTIFACT_BYTES = 512 * 1024 * 1024


@dataclass(frozen=True)
class ModelArtifactManifest:
    version: str
    symbol: str
    algorithm: str
    horizon_days: int
    artifact_file: str
    artifact_sha256: str
    validation_status: str
    validation_metrics: dict[str, float]
    created_at: str


class ModelArtifactStore:
    """Immutable model artifacts with checksum-verified atomic activation pointers."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root).expanduser().resolve()
        self._staged = self._root / "staged"
        self._active = self._root / "active"
        self._lock = RLock()

    def stage(
        self,
        *,
        version: str,
        symbol: str,
        algorithm: str,
        horizon_days: int,
        validation_status: str,
        validation_metrics: dict[str, float],
        write_artifact: Callable[[Path], None],
    ) -> ModelArtifactManifest:
        version = self._validate_version(version)
        symbol = self._validate_symbol(symbol)
        algorithm = self._validate_algorithm(algorithm)
        if not 1 <= horizon_days <= 365:
            raise ValueError("Model artifact horizon must be between 1 and 365 days")

        with self._lock:
            version_dir = self._staged / version
            manifest_path = version_dir / "manifest.json"
            if manifest_path.exists():
                existing = self.verify(version)
                self._assert_scope(existing, symbol, algorithm, horizon_days)
                return existing

            version_dir.mkdir(parents=True, exist_ok=False)
            artifact_path = version_dir / "model.ubj"
            temporary_path = version_dir / f".{uuid4().hex}.ubj"
            try:
                write_artifact(temporary_path)
                self._validate_artifact_file(temporary_path)
                digest = self._sha256(temporary_path)
                os.replace(temporary_path, artifact_path)
                manifest = ModelArtifactManifest(
                    version=version,
                    symbol=symbol,
                    algorithm=algorithm,
                    horizon_days=horizon_days,
                    artifact_file="model.ubj",
                    artifact_sha256=digest,
                    validation_status=validation_status,
                    validation_metrics={key: float(value) for key, value in validation_metrics.items()},
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
                self._atomic_json_write(manifest_path, asdict(manifest))
                return manifest
            except Exception:
                temporary_path.unlink(missing_ok=True)
                artifact_path.unlink(missing_ok=True)
                manifest_path.unlink(missing_ok=True)
                try:
                    version_dir.rmdir()
                except OSError:
                    pass
                raise

    def verify(
        self,
        version: str,
        *,
        symbol: str | None = None,
        algorithm: str | None = None,
        horizon_days: int | None = None,
    ) -> ModelArtifactManifest:
        version = self._validate_version(version)
        with self._lock:
            manifest_path = self._staged / version / "manifest.json"
            manifest = self._read_manifest(manifest_path)
            if manifest.version != version:
                raise ModelArtifactValidationError("Model artifact version does not match its path")
            if symbol is not None and algorithm is not None and horizon_days is not None:
                self._assert_scope(
                    manifest,
                    self._validate_symbol(symbol),
                    self._validate_algorithm(algorithm),
                    horizon_days,
                )
            artifact_path = self._safe_artifact_path(manifest_path.parent, manifest.artifact_file)
            self._validate_artifact_file(artifact_path)
            if self._sha256(artifact_path) != manifest.artifact_sha256:
                raise ModelArtifactValidationError("Model artifact checksum verification failed")
            return manifest

    def activate(
        self,
        version: str,
        *,
        symbol: str,
        algorithm: str,
        horizon_days: int,
    ) -> ModelArtifactManifest:
        with self._lock:
            manifest = self.verify(
                version,
                symbol=symbol,
                algorithm=algorithm,
                horizon_days=horizon_days,
            )
            pointer_path = self._pointer_path(symbol, algorithm, horizon_days)
            previous = self._read_json(pointer_path) if pointer_path.exists() else None
            pointer = {
                "version": manifest.version,
                "symbol": manifest.symbol,
                "algorithm": manifest.algorithm,
                "horizon_days": manifest.horizon_days,
                "activated_at": datetime.now(timezone.utc).isoformat(),
                "previous_version": previous.get("version") if previous else None,
            }
            self._atomic_json_write(pointer_path, pointer)
            return manifest

    def rollback(
        self,
        *,
        symbol: str,
        algorithm: str,
        horizon_days: int,
    ) -> ModelArtifactManifest:
        with self._lock:
            pointer_path = self._pointer_path(symbol, algorithm, horizon_days)
            if not pointer_path.exists():
                raise ModelArtifactValidationError("No active model exists for this scope")
            pointer = self._read_json(pointer_path)
            current_version = pointer.get("version")
            previous_version = pointer.get("previous_version")
            if not isinstance(current_version, str) or not isinstance(previous_version, str):
                raise ModelArtifactValidationError("No previous runtime model is available")
            manifest = self.verify(
                previous_version,
                symbol=symbol,
                algorithm=algorithm,
                horizon_days=horizon_days,
            )
            self._atomic_json_write(
                pointer_path,
                {
                    "version": previous_version,
                    "symbol": manifest.symbol,
                    "algorithm": manifest.algorithm,
                    "horizon_days": manifest.horizon_days,
                    "activated_at": datetime.now(timezone.utc).isoformat(),
                    "previous_version": current_version,
                },
            )
            return manifest

    def current(
        self,
        *,
        symbol: str,
        algorithm: str,
        horizon_days: int,
    ) -> ModelArtifactManifest | None:
        with self._lock:
            pointer_path = self._pointer_path(symbol, algorithm, horizon_days)
            if not pointer_path.exists():
                return None
            pointer = self._read_json(pointer_path)
            version = pointer.get("version")
            if not isinstance(version, str):
                raise ModelArtifactValidationError("Active model pointer has no version")
            return self.verify(
                version,
                symbol=symbol,
                algorithm=algorithm,
                horizon_days=horizon_days,
            )

    def artifact_path(self, manifest: ModelArtifactManifest) -> Path:
        return self._safe_artifact_path(
            self._staged / self._validate_version(manifest.version),
            manifest.artifact_file,
        )

    def _pointer_path(self, symbol: str, algorithm: str, horizon_days: int) -> Path:
        symbol = self._validate_symbol(symbol)
        algorithm = self._validate_algorithm(algorithm)
        scope = f"{symbol}|{algorithm}|{horizon_days}"
        return self._active / f"{sha256(scope.encode()).hexdigest()}.json"

    @staticmethod
    def _assert_scope(
        manifest: ModelArtifactManifest,
        symbol: str,
        algorithm: str,
        horizon_days: int,
    ) -> None:
        if (manifest.symbol, manifest.algorithm, manifest.horizon_days) != (
            symbol,
            algorithm,
            horizon_days,
        ):
            raise ModelArtifactValidationError("Model artifact scope does not match registry metadata")

    def _safe_artifact_path(self, directory: Path, relative_name: str) -> Path:
        if Path(relative_name).name != relative_name:
            raise ModelArtifactValidationError("Model artifact path must be a plain file name")
        path = (directory / relative_name).resolve(strict=True)
        try:
            path.relative_to(self._root)
        except ValueError as exc:
            raise ModelArtifactValidationError("Model artifact escapes the configured root") from exc
        if path.is_symlink():
            raise ModelArtifactValidationError("Symbolic model artifacts are not allowed")
        return path

    @staticmethod
    def _validate_artifact_file(path: Path) -> None:
        if not path.is_file() or path.is_symlink():
            raise ModelArtifactValidationError("Model artifact must be a regular file")
        size = path.stat().st_size
        if size <= 0 or size > _MAX_ARTIFACT_BYTES:
            raise ModelArtifactValidationError("Model artifact size is outside the allowed range")

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _read_manifest(self, path: Path) -> ModelArtifactManifest:
        payload = self._read_json(path)
        try:
            return ModelArtifactManifest(
                version=str(payload["version"]),
                symbol=self._validate_symbol(str(payload["symbol"])),
                algorithm=self._validate_algorithm(str(payload["algorithm"])),
                horizon_days=int(payload["horizon_days"]),
                artifact_file=str(payload["artifact_file"]),
                artifact_sha256=str(payload["artifact_sha256"]),
                validation_status=str(payload["validation_status"]),
                validation_metrics={
                    str(key): float(value)
                    for key, value in dict(payload["validation_metrics"]).items()
                },
                created_at=str(payload["created_at"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ModelArtifactValidationError("Model artifact manifest is invalid") from exc

    @staticmethod
    def _read_json(path: Path) -> dict:
        try:
            if path.stat().st_size > _MAX_MANIFEST_BYTES:
                raise ModelArtifactValidationError("Model artifact metadata is too large")
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ModelArtifactValidationError("Model artifact metadata cannot be read") from exc
        if not isinstance(payload, dict):
            raise ModelArtifactValidationError("Model artifact metadata must be an object")
        return payload

    @staticmethod
    def _atomic_json_write(path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("x", encoding="utf-8") as target:
                json.dump(payload, target, ensure_ascii=True, separators=(",", ":"))
                target.flush()
                os.fsync(target.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _validate_version(version: str) -> str:
        if not _VERSION_PATTERN.fullmatch(version):
            raise ValueError("Invalid model artifact version")
        return version

    @staticmethod
    def _validate_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not _SYMBOL_PATTERN.fullmatch(normalized):
            raise ValueError("Invalid model artifact symbol")
        return normalized

    @staticmethod
    def _validate_algorithm(algorithm: str) -> str:
        normalized = algorithm.strip().casefold()
        if not re.fullmatch(r"[a-z0-9_-]{1,32}", normalized):
            raise ValueError("Invalid model artifact algorithm")
        return normalized


class ModelArtifactValidationError(RuntimeError):
    pass
