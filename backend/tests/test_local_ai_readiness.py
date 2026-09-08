from pathlib import Path

from app.local_ai.model import LocalLogisticModel
from app.services.local_ai_readiness import LocalAiReadinessService


def _trained_model(agent: str) -> LocalLogisticModel:
    """서비스 테스트에 사용할 작고 결정적인 모델을 생성한다."""

    import numpy as np

    features = np.asarray([[float(i), float(i % 7)] for i in range(300)])
    labels = np.asarray([float(i % 2) for i in range(300)])
    return LocalLogisticModel.train(agent, ("trend", "cycle"), features, labels)


def test_readiness_reports_missing_artifacts_without_exposing_path(tmp_path: Path):
    service = LocalAiReadinessService(tmp_path, enabled=False)

    result = service.summary()

    assert result["enabled"] is False
    assert result["summary"]["missing"] == 8
    assert result["summary"]["core_ready"] is False
    assert "artifact_dir" not in result


def test_readiness_uses_checksum_and_quality_gate(tmp_path: Path):
    model = _trained_model("technical")
    model.save(tmp_path / "technical.json")
    service = LocalAiReadinessService(tmp_path, enabled=True)

    item = service.summary()["items"][0]

    assert item["agent"] == "technical"
    assert item["status"] == "quality_rejected"
    assert item["training_samples"] == 300
    assert item["model_version"].startswith("local-technical-")
    assert "coefficients" not in item


def test_readiness_fails_closed_for_tampered_artifact(tmp_path: Path):
    path = tmp_path / "technical.json"
    _trained_model("technical").save(path)
    path.write_text(path.read_text(encoding="utf-8").replace("trend", "tampered"), encoding="utf-8")

    item = LocalAiReadinessService(tmp_path, enabled=True).summary()["items"][0]

    assert item["status"] == "artifact_invalid"
    assert item["reasons"] == ["artifact_integrity_check_failed"]
