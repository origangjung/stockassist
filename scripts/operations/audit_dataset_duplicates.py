"""Find exact duplicate dataset files without deleting or exposing their contents."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = Path("artifacts/workspace-cleanup/dataset-duplicates.json")
PROTECTED_DATASET_NAMES = {"local-ai", "local-ai-incremental"}
HASH_CHUNK_BYTES = 1024 * 1024


def parse_args() -> argparse.Namespace:
    """Parse the workspace root and JSON report destination."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def resolve_output(root: Path, output: Path) -> Path:
    """Restrict duplicate reports to the workspace artifacts directory."""

    root = root.resolve()
    destination = (root / output).resolve() if not output.is_absolute() else output.resolve()
    artifacts = (root / "artifacts").resolve()
    if destination.suffix.lower() != ".json" or not destination.is_relative_to(artifacts):
        raise ValueError("output must be a JSON file inside the workspace artifacts directory")
    return destination


def dataset_files(root: Path) -> list[Path]:
    """List regular dataset files without following directory or file links."""

    datasets = root / "datasets"
    if not datasets.is_dir() or datasets.is_symlink():
        return []

    files: list[Path] = []
    for current, directories, names in os.walk(datasets, followlinks=False):
        current_path = Path(current)
        directories[:] = [name for name in directories if not (current_path / name).is_symlink()]
        for name in names:
            path = current_path / name
            if path.is_file() and not path.is_symlink():
                files.append(path)
    return sorted(files)


def sha256_file(path: Path) -> str:
    """Stream a file into SHA-256 so large CSV files do not fill memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(HASH_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def is_protected(root: Path, path: Path) -> bool:
    """Return whether a file belongs to an active dataset directory."""

    relative = path.relative_to(root)
    return len(relative.parts) >= 2 and relative.parts[1] in PROTECTED_DATASET_NAMES


def choose_keeper(root: Path, files: list[Path]) -> tuple[Path, str]:
    """Prefer active data, then the newest historical copy, as the keeper."""

    protected = [path for path in files if is_protected(root, path)]
    candidates = protected or files
    keeper = sorted(
        candidates,
        key=lambda path: (-path.stat().st_mtime_ns, path.relative_to(root).as_posix()),
    )[0]
    reason = "active_dataset" if protected else "newest_historical_copy"
    return keeper, reason


def build_duplicate_report(root: Path) -> dict[str, object]:
    """Hash same-sized files and describe only byte-for-byte duplicate groups."""

    root = root.resolve()
    files = dataset_files(root)
    by_size: dict[int, list[Path]] = defaultdict(list)
    for path in files:
        by_size[path.stat().st_size].append(path)

    by_identity: dict[tuple[int, str], list[Path]] = defaultdict(list)
    hashed_files = 0
    hashed_bytes = 0
    for size, candidates in by_size.items():
        if len(candidates) < 2:
            continue
        for path in candidates:
            by_identity[(size, sha256_file(path))].append(path)
            hashed_files += 1
            hashed_bytes += size

    groups: list[dict[str, object]] = []
    reclaimable_bytes = 0
    for (size, digest), duplicates in by_identity.items():
        if len(duplicates) < 2:
            continue
        keeper, reason = choose_keeper(root, duplicates)
        removable = sorted(
            path.relative_to(root).as_posix() for path in duplicates if path != keeper
        )
        reclaimable = size * len(removable)
        reclaimable_bytes += reclaimable
        groups.append(
            {
                "sha256": digest,
                "file_bytes": size,
                "copies": len(duplicates),
                "keeper": keeper.relative_to(root).as_posix(),
                "keeper_reason": reason,
                "review_candidates": removable,
                "potential_reclaim_bytes": reclaimable,
            }
        )

    groups.sort(key=lambda group: int(group["potential_reclaim_bytes"]), reverse=True)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "automatic_deletion": False,
        "method": "same_size_and_sha256",
        "summary": {
            "dataset_files": len(files),
            "hashed_files": hashed_files,
            "hashed_bytes": hashed_bytes,
            "duplicate_groups": len(groups),
            "potential_reclaim_bytes": reclaimable_bytes,
        },
        "groups": groups,
    }


def write_report(destination: Path, report: dict[str, object]) -> None:
    """Atomically write the duplicate audit as JSON."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, destination)


def main() -> int:
    """Audit datasets, persist the result, and print a compact summary."""

    args = parse_args()
    root = args.root.resolve()
    destination = resolve_output(root, args.output)
    report = build_duplicate_report(root)
    write_report(destination, report)
    summary = report["summary"]
    print(f"report={destination.relative_to(root).as_posix()}")
    print(f"dataset_files={summary['dataset_files']}")
    print(f"duplicate_groups={summary['duplicate_groups']}")
    print(f"potential_reclaim_bytes={summary['potential_reclaim_bytes']}")
    print("automatic_deletion=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
