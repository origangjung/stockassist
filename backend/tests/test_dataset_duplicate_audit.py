"""Verify exact dataset duplicate auditing and keeper selection."""

from pathlib import Path

from scripts.operations.audit_dataset_duplicates import build_duplicate_report


def write_fixture(path: Path, content: bytes, mtime_ns: int) -> None:
    """Create one dataset fixture with a deterministic modification time."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    path.touch()
    path.chmod(0o600)
    import os

    os.utime(path, ns=(mtime_ns, mtime_ns))


def test_report_finds_exact_duplicates_and_keeps_active_data(tmp_path: Path) -> None:
    """An active copy is kept even when a historical copy is newer."""

    active = tmp_path / "datasets" / "local-ai-incremental" / "features.csv"
    historical = tmp_path / "datasets" / "experiment-v1" / "features.csv"
    different = tmp_path / "datasets" / "experiment-v2" / "features.csv"
    write_fixture(active, b"same-data", 1)
    write_fixture(historical, b"same-data", 2)
    write_fixture(different, b"other-row", 3)

    report = build_duplicate_report(tmp_path)

    assert report["automatic_deletion"] is False
    assert report["summary"]["dataset_files"] == 3
    assert report["summary"]["duplicate_groups"] == 1
    assert report["summary"]["potential_reclaim_bytes"] == len(b"same-data")
    group = report["groups"][0]
    assert group["keeper"] == "datasets/local-ai-incremental/features.csv"
    assert group["keeper_reason"] == "active_dataset"
    assert group["review_candidates"] == ["datasets/experiment-v1/features.csv"]
    assert active.exists() and historical.exists() and different.exists()


def test_report_keeps_newest_historical_copy(tmp_path: Path) -> None:
    """The newest copy is suggested when no active dataset owns the file."""

    old = tmp_path / "datasets" / "experiment-old" / "data.csv"
    new = tmp_path / "datasets" / "experiment-new" / "data.csv"
    write_fixture(old, b"duplicate", 1)
    write_fixture(new, b"duplicate", 2)

    group = build_duplicate_report(tmp_path)["groups"][0]

    assert group["keeper"] == "datasets/experiment-new/data.csv"
    assert group["keeper_reason"] == "newest_historical_copy"
