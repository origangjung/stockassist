"""Classify exact duplicate datasets by code, metadata, and documentation references."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DUPLICATES = Path("artifacts/workspace-cleanup/dataset-duplicates.json")
DEFAULT_OUTPUT = Path("artifacts/workspace-cleanup/dataset-reference-audit.json")
MAX_TEXT_BYTES = 5 * 1024 * 1024
SOURCE_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".ps1",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}
SOURCE_ROOTS = ("backend", "frontend", "scripts", "docs", "infrastructure")
SKIPPED_PARTS = {
    ".git",
    ".next",
    ".venv",
    "artifacts",
    "node_modules",
    "playwright-report",
    "test-results",
}


def parse_args() -> argparse.Namespace:
    """Parse workspace, duplicate report, and output paths."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--duplicates", type=Path, default=DEFAULT_DUPLICATES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def resolve_inside(root: Path, path: Path, allowed: Path) -> Path:
    """Resolve a JSON path and require it to stay in an allowed workspace directory."""

    root = root.resolve()
    destination = (root / path).resolve() if not path.is_absolute() else path.resolve()
    boundary = (root / allowed).resolve()
    if destination.suffix.lower() != ".json" or not destination.is_relative_to(boundary):
        raise ValueError(f"JSON path must remain inside {allowed.as_posix()}")
    return destination


def walk_text_files(root: Path) -> list[tuple[Path, str]]:
    """Read bounded source and dataset metadata files, excluding secrets and generated output."""

    files: list[tuple[Path, str]] = []
    for root_name in SOURCE_ROOTS:
        base = root / root_name
        if not base.is_dir() or base.is_symlink():
            continue
        for current, directories, names in os.walk(base, followlinks=False):
            current_path = Path(current)
            directories[:] = [
                name
                for name in directories
                if name not in SKIPPED_PARTS and not (current_path / name).is_symlink()
            ]
            for name in names:
                path = current_path / name
                if (
                    name.startswith(".env")
                    or path.suffix.lower() not in SOURCE_SUFFIXES
                    or path.is_symlink()
                    or path.stat().st_size > MAX_TEXT_BYTES
                ):
                    continue
                files.append((path, "documentation" if root_name == "docs" else "runtime"))

    for path in sorted((root / "datasets").rglob("*.json")):
        if path.is_file() and not path.is_symlink() and path.stat().st_size <= MAX_TEXT_BYTES:
            files.append((path, "dataset_metadata"))

    for path in root.iterdir():
        if (
            path.is_file()
            and not path.is_symlink()
            and not path.name.startswith(".env")
            and path.suffix.lower() in SOURCE_SUFFIXES
            and path.stat().st_size <= MAX_TEXT_BYTES
        ):
            files.append((path, "runtime" if path.name != "README.md" else "documentation"))
    return files


def candidate_references(
    root: Path,
    candidate: Path,
    scanned_files: list[tuple[Path, str]],
) -> dict[str, list[str]]:
    """Return reference file paths by type without returning matched file contents."""

    relative = candidate.as_posix()
    directory = candidate.parent.as_posix()
    references: dict[str, list[str]] = {
        "runtime": [],
        "dataset_metadata": [],
        "documentation": [],
    }
    for source, reference_type in scanned_files:
        text = source.read_text(encoding="utf-8", errors="ignore").replace("\\", "/")
        is_same_dataset_metadata = (
            reference_type == "dataset_metadata"
            and source.parent.resolve() == (root / candidate.parent).resolve()
        )
        if relative in text or directory in text or (is_same_dataset_metadata and candidate.name in text):
            references[reference_type].append(source.relative_to(root).as_posix())
    return {kind: sorted(set(paths)) for kind, paths in references.items()}


def disposition(references: dict[str, list[str]]) -> str:
    """Choose a conservative review status from the strongest reference type."""

    if references["runtime"] or references["dataset_metadata"]:
        return "retain_referenced"
    if references["documentation"]:
        return "retain_for_reproducibility_review"
    return "unreferenced_review_candidate"


def build_reference_audit(root: Path, duplicate_report: dict[str, object]) -> dict[str, object]:
    """Audit every duplicate review candidate against safe text sources."""

    root = root.resolve()
    scanned_files = walk_text_files(root)
    entries: list[dict[str, object]] = []
    for group in duplicate_report.get("groups", []):
        for value in group.get("review_candidates", []):
            candidate = Path(value)
            references = candidate_references(root, candidate, scanned_files)
            entries.append(
                {
                    "path": candidate.as_posix(),
                    "file_bytes": int(group["file_bytes"]),
                    "sha256": group["sha256"],
                    "keeper": group["keeper"],
                    "references": references,
                    "disposition": disposition(references),
                }
            )

    entries.sort(key=lambda entry: int(entry["file_bytes"]), reverse=True)
    counts = {
        status: sum(entry["disposition"] == status for entry in entries)
        for status in (
            "retain_referenced",
            "retain_for_reproducibility_review",
            "unreferenced_review_candidate",
        )
    }
    unreferenced_bytes = sum(
        int(entry["file_bytes"])
        for entry in entries
        if entry["disposition"] == "unreferenced_review_candidate"
    )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "automatic_deletion": False,
        "summary": {
            "scanned_text_files": len(scanned_files),
            "duplicate_candidates": len(entries),
            "disposition_counts": counts,
            "unreferenced_candidate_bytes": unreferenced_bytes,
        },
        "entries": entries,
    }


def write_report(destination: Path, report: dict[str, object]) -> None:
    """Atomically write the metadata-only reference report."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, destination)


def main() -> int:
    """Load duplicate candidates, audit references, and persist the result."""

    args = parse_args()
    root = args.root.resolve()
    duplicates = resolve_inside(root, args.duplicates, Path("artifacts"))
    output = resolve_inside(root, args.output, Path("artifacts"))
    duplicate_report = json.loads(duplicates.read_text(encoding="utf-8"))
    report = build_reference_audit(root, duplicate_report)
    write_report(output, report)
    summary = report["summary"]
    print(f"report={output.relative_to(root).as_posix()}")
    print(f"duplicate_candidates={summary['duplicate_candidates']}")
    print(f"disposition_counts={json.dumps(summary['disposition_counts'], sort_keys=True)}")
    print(f"unreferenced_candidate_bytes={summary['unreferenced_candidate_bytes']}")
    print("automatic_deletion=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
