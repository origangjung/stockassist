"""Verify conservative duplicate dataset reference classification."""

from pathlib import Path

from scripts.operations.audit_dataset_references import build_reference_audit


def duplicate_report(paths: list[str]) -> dict[str, object]:
    """Build a minimal exact-duplicate report fixture."""

    return {
        "groups": [
            {
                "file_bytes": 10,
                "sha256": "abc",
                "keeper": "datasets/local-ai/keeper.csv",
                "review_candidates": paths,
            }
        ]
    }


def write_text(path: Path, value: str) -> None:
    """Create one UTF-8 text fixture."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def test_runtime_and_metadata_references_are_retained(tmp_path: Path) -> None:
    """Code and same-directory metadata references block cleanup candidacy."""

    runtime_path = "datasets/experiment-runtime/data.csv"
    metadata_path = "datasets/experiment-metadata/data.csv"
    write_text(tmp_path / "scripts" / "train.py", f'DATA = "{runtime_path}"')
    write_text(tmp_path / metadata_path, "rows")
    write_text(tmp_path / "datasets" / "experiment-metadata" / "manifest.json", '"data.csv"')

    report = build_reference_audit(tmp_path, duplicate_report([runtime_path, metadata_path]))
    entries = {entry["path"]: entry for entry in report["entries"]}

    assert entries[runtime_path]["disposition"] == "retain_referenced"
    assert entries[metadata_path]["disposition"] == "retain_referenced"
    assert entries[metadata_path]["references"]["dataset_metadata"] == [
        "datasets/experiment-metadata/manifest.json"
    ]


def test_documented_and_unreferenced_candidates_remain_separate(tmp_path: Path) -> None:
    """Documentation and no-reference candidates receive different manual review states."""

    documented = "datasets/experiment-documented/data.csv"
    unreferenced = "datasets/experiment-unused/data.csv"
    write_text(tmp_path / "docs" / "run.md", f"Replay `{documented}`.")
    write_text(tmp_path / ".env", unreferenced)

    report = build_reference_audit(tmp_path, duplicate_report([documented, unreferenced]))
    entries = {entry["path"]: entry for entry in report["entries"]}

    assert entries[documented]["disposition"] == "retain_for_reproducibility_review"
    assert entries[unreferenced]["disposition"] == "unreferenced_review_candidate"
    assert report["summary"]["unreferenced_candidate_bytes"] == 10
    assert (tmp_path / ".env").exists()
