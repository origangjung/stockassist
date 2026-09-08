from pathlib import Path

import pytest

from scripts.operations.soak_kis_realtime import normalized_symbols, safe_output_path


def test_kis_soak_normalizes_and_bounds_symbols():
    assert normalized_symbols(["005930", "aapl", "AAPL"]) == ["005930", "AAPL"]
    with pytest.raises(ValueError):
        normalized_symbols(["AAPL;whoami"])


def test_kis_soak_report_stays_in_ignored_artifact_root(tmp_path, monkeypatch):
    root = (tmp_path / "artifacts" / "realtime-validation").resolve()
    root.mkdir(parents=True)
    monkeypatch.setattr("scripts.operations.soak_kis_realtime.ARTIFACT_ROOT", root)

    assert safe_output_path(root / "report.json") == root / "report.json"
    with pytest.raises(ValueError):
        safe_output_path(Path(tmp_path / "outside.json"))
