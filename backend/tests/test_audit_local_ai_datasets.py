import csv
from datetime import datetime, timedelta

import pytest

from scripts.ai.training.audit_local_ai_datasets import audit, safe_report_path, save_report


def _write_dataset(path, rows):
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=["timestamp", "symbol", "feature", "label"],
        )
        writer.writeheader()
        writer.writerows(rows)


def _rows(count):
    start = datetime(2020, 1, 1)
    return [
        {
            "timestamp": (start + timedelta(hours=index)).isoformat(),
            "symbol": ("AAPL", "MSFT", "NVDA")[index % 3],
            "feature": index / max(count, 1),
            "label": index % 2,
        }
        for index in range(count)
    ]


def test_audit_separates_structural_quality_from_training_readiness(tmp_path):
    path = tmp_path / "news.csv"
    _write_dataset(path, _rows(100))

    result = audit(path, ("feature",), minimum_validation_samples=200)

    assert result["status"] == "ok"
    assert result["training_readiness"] == "collect_more_data"
    assert "validation_rows<200" in result["readiness_reasons"]


def test_audit_marks_sufficient_balanced_history_ready_for_candidate_training(tmp_path):
    path = tmp_path / "financial.csv"
    _write_dataset(path, _rows(1_000))

    result = audit(path, ("feature",), minimum_validation_samples=200)

    assert result["status"] == "ok"
    assert result["validation_rows"] == 200
    assert result["training_readiness"] == "ready_for_candidate_training"
    assert result["readiness_reasons"] == []


def test_audit_report_stays_inside_dataset_directory_and_saves_atomically(tmp_path):
    report_path = safe_report_path(tmp_path, tmp_path / "dataset-readiness.json")

    save_report(report_path, {"news": {"status": "ok"}})

    assert '"status": "ok"' in report_path.read_text(encoding="utf-8")
    assert list(tmp_path.glob(".*.tmp")) == []
    with pytest.raises(ValueError, match="inside the data directory"):
        safe_report_path(tmp_path, tmp_path.parent / "outside.json")
