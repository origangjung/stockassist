"""Fail CI when Git tracks likely secrets, local data, or generated artifacts.

The check examines tracked path names and file sizes only. It deliberately does
not read file contents, so running it cannot print credentials from a local
untracked .env file.
"""

from __future__ import annotations

import subprocess
from pathlib import Path, PurePosixPath


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MAX_TRACKED_FILE_BYTES = 10 * 1024 * 1024

FORBIDDEN_DIRECTORY_NAMES = {
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "artifacts",
    "backups",
    "node_modules",
    "postgres-data",
    "redis-data",
}
FORBIDDEN_SUFFIXES = {
    ".backup",
    ".db",
    ".dump",
    ".key",
    ".p12",
    ".pem",
    ".pfx",
    ".sqlite",
    ".sqlite3",
    ".tsbuildinfo",
}


def tracked_paths() -> list[PurePosixPath]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
    )
    return [
        PurePosixPath(item.decode("utf-8", errors="surrogateescape"))
        for item in result.stdout.split(b"\0")
        if item
    ]


def path_violation(path: PurePosixPath) -> str | None:
    lowered_parts = tuple(part.lower() for part in path.parts)
    name = lowered_parts[-1]

    if name != ".env.example" and (
        name == ".env" or name.startswith(".env.") or name.endswith(".env")
    ):
        return "environment file"
    if any(part in FORBIDDEN_DIRECTORY_NAMES for part in lowered_parts[:-1]):
        return "generated or local-data directory"
    if any(name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
        return "secret, database, backup, or generated file type"
    if (name.startswith("credentials") or name.startswith("secrets")) and name.endswith(
        ".json"
    ):
        return "credential-like JSON file"
    return None


def main() -> int:
    violations: list[str] = []
    for path in tracked_paths():
        reason = path_violation(path)
        local_path = REPOSITORY_ROOT.joinpath(*path.parts)
        if reason is None and local_path.is_file():
            size = local_path.stat().st_size
            if size > MAX_TRACKED_FILE_BYTES:
                reason = f"file exceeds {MAX_TRACKED_FILE_BYTES // (1024 * 1024)} MiB"
        if reason is not None:
            violations.append(f"{path.as_posix()}: {reason}")

    if violations:
        print("Repository hygiene check failed:")
        for violation in violations:
            print(f"- {violation}")
        print("Move secrets to .env/Secret Manager and generated data outside Git.")
        return 1

    print("Repository hygiene check passed (tracked path names and sizes only).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
