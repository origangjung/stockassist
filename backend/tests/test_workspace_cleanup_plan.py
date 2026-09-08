"""Verify the metadata-only workspace cleanup planner."""

from pathlib import Path

import pytest

from scripts.operations.plan_workspace_cleanup import build_plan, resolve_output


def write_bytes(path: Path, size: int) -> None:
    """Create a small fixture file with a predictable size."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


def test_build_plan_classifies_paths_without_removing_them(tmp_path: Path) -> None:
    """Caches may be reclaimable, while active and historical datasets stay protected."""

    cache = tmp_path / "frontend" / ".next" / "cache.bin"
    active = tmp_path / "datasets" / "local-ai-incremental" / "latest.csv"
    historical = tmp_path / "datasets" / "experiment-v1" / "features.csv"
    dependency = tmp_path / ".venv" / "package.bin"
    for path, size in ((cache, 11), (active, 13), (historical, 17), (dependency, 19)):
        write_bytes(path, size)

    plan = build_plan(tmp_path)
    items = {entry["path"]: entry for entry in plan["items"]}

    assert plan["automatic_deletion"] is False
    assert plan["summary"]["rebuildable_cache_bytes"] == 11
    assert plan["summary"]["historical_dataset_bytes"] == 17
    assert items["frontend/.next"]["action"] == "safe_to_remove_after_approval"
    assert items["datasets/local-ai-incremental"]["action"] == "protect"
    assert items["datasets/experiment-v1"]["action"] == "manual_review_required"
    assert items[".venv"]["action"] == "keep_for_ready_environment"
    assert cache.exists() and active.exists() and historical.exists() and dependency.exists()


def test_build_plan_does_not_follow_symlink(tmp_path: Path) -> None:
    """Linked content outside the workspace must not contribute to reported bytes."""

    external = tmp_path.parent / f"{tmp_path.name}-external.bin"
    write_bytes(external, 23)
    link = tmp_path / "frontend" / ".next"
    link.parent.mkdir(parents=True)
    try:
        link.symlink_to(external)
    except OSError:
        pytest.skip("symbolic links are unavailable for this Windows user")

    plan = build_plan(tmp_path)
    item = next(entry for entry in plan["items"] if entry["path"] == "frontend/.next")

    assert item["bytes"] == 0
    assert external.exists()


def test_resolve_output_restricts_reports_to_artifacts(tmp_path: Path) -> None:
    """Report destinations outside artifacts or with non-JSON suffixes are rejected."""

    expected = tmp_path / "artifacts" / "workspace-cleanup" / "latest.json"

    assert resolve_output(tmp_path, Path("artifacts/workspace-cleanup/latest.json")) == expected
    with pytest.raises(ValueError):
        resolve_output(tmp_path, Path("cleanup.json"))
    with pytest.raises(ValueError):
        resolve_output(tmp_path, Path("artifacts/cleanup.txt"))
