import json

import pytest

from app.prediction.artifacts import ModelArtifactStore, ModelArtifactValidationError


def _write_artifact(path):
    path.write_bytes(b"bounded-test-model")


def test_model_artifact_activation_is_checksum_verified_and_scope_bound(tmp_path):
    store = ModelArtifactStore(tmp_path / "models")
    staged = store.stage(
        version="xgb-test-001",
        symbol="005930",
        algorithm="xgboost",
        horizon_days=5,
        validation_status="experimental",
        validation_metrics={"accuracy": 0.61, "validation_samples": 40},
        write_artifact=_write_artifact,
    )

    assert store.current(symbol="005930", algorithm="xgboost", horizon_days=5) is None
    activated = store.activate(
        staged.version,
        symbol="005930",
        algorithm="xgboost",
        horizon_days=5,
    )

    assert activated.artifact_sha256 == staged.artifact_sha256
    assert store.current(symbol="005930", algorithm="xgboost", horizon_days=5) == staged
    with pytest.raises(ModelArtifactValidationError, match="scope"):
        store.activate(
            staged.version,
            symbol="AAPL",
            algorithm="xgboost",
            horizon_days=5,
        )


def test_model_artifact_tampering_fails_closed(tmp_path):
    store = ModelArtifactStore(tmp_path / "models")
    manifest = store.stage(
        version="xgb-test-002",
        symbol="AAPL",
        algorithm="xgboost",
        horizon_days=5,
        validation_status="experimental",
        validation_metrics={"accuracy": 0.55},
        write_artifact=_write_artifact,
    )
    store.artifact_path(manifest).write_bytes(b"tampered")

    with pytest.raises(ModelArtifactValidationError, match="checksum"):
        store.verify(manifest.version)


def test_model_artifact_runtime_pointer_can_rollback_atomically(tmp_path):
    store = ModelArtifactStore(tmp_path / "models")
    for version in ("xgb-old", "xgb-new"):
        store.stage(
            version=version,
            symbol="AAPL",
            algorithm="xgboost",
            horizon_days=5,
            validation_status="experimental",
            validation_metrics={"accuracy": 0.6},
            write_artifact=lambda path, value=version: path.write_bytes(value.encode()),
        )
        store.activate(version, symbol="AAPL", algorithm="xgboost", horizon_days=5)

    rolled_back = store.rollback(symbol="AAPL", algorithm="xgboost", horizon_days=5)

    assert rolled_back.version == "xgb-old"
    assert store.current(symbol="AAPL", algorithm="xgboost", horizon_days=5).version == "xgb-old"


def test_model_artifact_manifest_rejects_path_traversal(tmp_path):
    store = ModelArtifactStore(tmp_path / "models")
    manifest = store.stage(
        version="xgb-test-003",
        symbol="MSFT",
        algorithm="xgboost",
        horizon_days=5,
        validation_status="experimental",
        validation_metrics={"accuracy": 0.58},
        write_artifact=_write_artifact,
    )
    manifest_path = tmp_path / "models" / "staged" / manifest.version / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["artifact_file"] = "../outside.ubj"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ModelArtifactValidationError, match="plain file name"):
        store.verify(manifest.version)
