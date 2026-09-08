"""Create a non-destructive workspace storage cleanup plan.

The planner reads path metadata only. It never reads file contents and has no
delete mode, so datasets and local credentials cannot be exposed or removed.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = Path("artifacts/workspace-cleanup/latest.json")

REBUILDABLE_CACHES = (
    Path("frontend/.next"),
    Path("frontend/test-results"),
    Path("frontend/playwright-report"),
    Path(".pytest_cache"),
    Path(".ruff_cache"),
    Path("coverage"),
    Path("htmlcov"),
    Path("dist"),
    Path("build"),
)
DEPENDENCY_DIRECTORIES = (Path(".venv"), Path("node_modules"), Path("frontend/node_modules"))
PROTECTED_DATASET_NAMES = {"local-ai", "local-ai-incremental"}


def parse_args() -> argparse.Namespace:
    """Parse the workspace root and JSON report destination."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def directory_size(path: Path) -> int:
    """Return regular-file bytes without following links outside the workspace."""

    if path.is_symlink():
        return 0
    if path.is_file():
        return path.stat().st_size
    if not path.is_dir():
        return 0

    total = 0
    for current, directories, files in os.walk(path, followlinks=False):
        current_path = Path(current)
        directories[:] = [name for name in directories if not (current_path / name).is_symlink()]
        for name in files:
            candidate = current_path / name
            if not candidate.is_symlink():
                total += candidate.stat().st_size
    return total


def item(root: Path, relative: Path, category: str, action: str) -> dict[str, object] | None:
    """Build one metadata-only report item for an existing path."""

    path = root / relative
    if not path.exists() and not path.is_symlink():
        return None
    return {
        "path": relative.as_posix(),
        "bytes": directory_size(path),
        "category": category,
        "action": action,
    }


def build_plan(root: Path) -> dict[str, object]:
    """Classify generated caches, dependencies, and datasets by cleanup safety."""

    root = root.resolve()
    items: list[dict[str, object]] = []

    for relative in REBUILDABLE_CACHES:
        planned = item(root, relative, "rebuildable_cache", "safe_to_remove_after_approval")
        if planned:
            items.append(planned)

    seen_dependencies: set[Path] = set()
    for relative in DEPENDENCY_DIRECTORIES:
        path = root / relative
        if any(parent in seen_dependencies for parent in path.parents):
            continue
        planned = item(root, relative, "installed_dependency", "keep_for_ready_environment")
        if planned:
            items.append(planned)
            seen_dependencies.add(path)

    datasets = root / "datasets"
    if datasets.is_dir() and not datasets.is_symlink():
        for path in sorted(datasets.iterdir(), key=lambda candidate: candidate.name.lower()):
            if path.is_symlink() or not path.is_dir():
                continue
            protected = path.name in PROTECTED_DATASET_NAMES
            items.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "bytes": directory_size(path),
                    "category": "active_dataset" if protected else "historical_dataset",
                    "action": "protect" if protected else "manual_review_required",
                }
            )

    reclaimable = sum(
        int(entry["bytes"]) for entry in items if entry["category"] == "rebuildable_cache"
    )
    historical = sum(
        int(entry["bytes"]) for entry in items if entry["category"] == "historical_dataset"
    )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "automatic_deletion": False,
        "summary": {
            "rebuildable_cache_bytes": reclaimable,
            "historical_dataset_bytes": historical,
            "item_count": len(items),
        },
        "items": sorted(items, key=lambda entry: int(entry["bytes"]), reverse=True),
    }


def resolve_output(root: Path, output: Path) -> Path:
    """Restrict reports to the workspace artifacts directory."""

    root = root.resolve()
    destination = (root / output).resolve() if not output.is_absolute() else output.resolve()
    artifacts = (root / "artifacts").resolve()
    if destination.suffix.lower() != ".json" or not destination.is_relative_to(artifacts):
        raise ValueError("output must be a JSON file inside the workspace artifacts directory")
    return destination


def write_report(destination: Path, plan: dict[str, object]) -> None:
    """Atomically write the cleanup plan without exposing file contents."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, destination)


def main() -> int:
    """Create the report and print the only automatically reclaimable total."""

    args = parse_args()
    root = args.root.resolve()
    destination = resolve_output(root, args.output)
    plan = build_plan(root)
    write_report(destination, plan)
    summary = plan["summary"]
    print(f"report={destination.relative_to(root).as_posix()}")
    print(f"rebuildable_cache_bytes={summary['rebuildable_cache_bytes']}")
    print(f"historical_dataset_bytes={summary['historical_dataset_bytes']}")
    print("automatic_deletion=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
