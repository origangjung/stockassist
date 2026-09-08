import csv

from app.local_ai.kis_flow_features import KIS_FLOW_FEATURES
from scripts.ai.data.build_kis_flow_local_ai_dataset import (
    _load_compatible_rows,
    _read_rows,
)


def test_resume_discards_rows_from_an_incomplete_feature_schema(tmp_path):
    path = tmp_path / "investor_flow.csv"
    fieldnames = ["timestamp", "symbol", *KIS_FLOW_FEATURES, "label"]
    complete = {name: "0.1" for name in KIS_FLOW_FEATURES}
    incomplete = {**complete, KIS_FLOW_FEATURES[-1]: ""}
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {"timestamp": "2026-01-01", "symbol": "005930", **complete, "label": "1"}
        )
        writer.writerow(
            {"timestamp": "2026-01-02", "symbol": "005930", **incomplete, "label": "0"}
        )

    rows = _read_rows(path)

    assert len(rows) == 1
    assert rows[0]["timestamp"] == "2026-01-01"


def test_legacy_five_day_rows_are_archived_before_ten_day_collection(tmp_path):
    path = tmp_path / "investor_flow.csv"
    complete = {name: "0.1" for name in KIS_FLOW_FEATURES}
    fieldnames = ["timestamp", "symbol", *KIS_FLOW_FEATURES, "label"]
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {"timestamp": "2026-01-01", "symbol": "005930", **complete, "label": "1"}
        )

    rows = _load_compatible_rows(path, horizon_days=10, resume=True)

    assert rows == []
    assert (tmp_path / "investor_flow-legacy-5d.csv").read_bytes() == path.read_bytes()
