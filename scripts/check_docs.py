"""Validate local Markdown links and current Alembic head references."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIRECTORY = REPOSITORY_ROOT / "backend" / "alembic" / "versions"
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
HEAD_MARKER = re.compile(r"<!--\s*current-alembic-head:\s*([0-9]{8}_[0-9]{4})\s*-->")
CURRENT_HEAD_REFERENCES = (
    re.compile(r"alembic heads` reports `([0-9]{8}_[0-9]{4})`", re.IGNORECASE),
    re.compile(r"Alembic revision `([0-9]{8}_[0-9]{4})`가 현재 head"),
    re.compile(r"Alembic: `([0-9]{8}_[0-9]{4}) \(head\)`", re.IGNORECASE),
)


def markdown_documents(root: Path = REPOSITORY_ROOT) -> list[Path]:
    documents = [
        path
        for name in ("README.md", "PROJECT_INTRODUCTION.md", "DESKTOP_CODEX_HANDOFF.md")
        if (path := root / name).is_file()
    ]
    docs_root = root / "docs"
    if docs_root.is_dir():
        documents.extend(sorted(docs_root.rglob("*.md")))
    return documents


def broken_local_links(documents: list[Path], root: Path) -> list[str]:
    violations: list[str] = []
    resolved_root = root.resolve()
    for document in documents:
        text = document.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(text):
            raw_target = match.group(1).strip()
            if raw_target.startswith("<") and raw_target.endswith(">"):
                raw_target = raw_target[1:-1]
            target = raw_target.split(maxsplit=1)[0]
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith("#"):
                continue
            local_target = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not local_target:
                continue
            candidate = (
                resolved_root / local_target.lstrip("/")
                if local_target.startswith("/")
                else document.parent / local_target
            ).resolve()
            line = text.count("\n", 0, match.start()) + 1
            try:
                candidate.relative_to(resolved_root)
            except ValueError:
                violations.append(f"{document.relative_to(root)}:{line}: link leaves repository")
                continue
            if not candidate.exists():
                violations.append(
                    f"{document.relative_to(root)}:{line}: missing local link {local_target}"
                )
    return violations


def _assignment_value(tree: ast.Module, name: str):
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in statement.targets
        ):
            return ast.literal_eval(statement.value)
    raise ValueError(f"missing {name} assignment")


def migration_heads(directory: Path = MIGRATION_DIRECTORY) -> set[str]:
    revisions: set[str] = set()
    parents: set[str] = set()
    for path in sorted(directory.glob("*.py")):
        if path.name.startswith("__"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        revision = _assignment_value(tree, "revision")
        down_revision = _assignment_value(tree, "down_revision")
        if not isinstance(revision, str) or not revision:
            raise ValueError(f"{path.name}: invalid revision")
        if revision in revisions:
            raise ValueError(f"{path.name}: duplicate revision {revision}")
        revisions.add(revision)
        if isinstance(down_revision, str):
            parents.add(down_revision)
        elif isinstance(down_revision, (tuple, list)):
            parents.update(item for item in down_revision if isinstance(item, str))
        elif down_revision is not None:
            raise ValueError(f"{path.name}: invalid down_revision")
    missing_parents = parents - revisions
    if missing_parents:
        raise ValueError(f"missing parent revisions: {', '.join(sorted(missing_parents))}")
    return revisions - parents


def migration_head_reference_violations(
    documents: list[Path], expected_head: str, root: Path = REPOSITORY_ROOT
) -> list[str]:
    violations: list[str] = []
    markers = 0
    for document in documents:
        text = document.read_text(encoding="utf-8")
        for match in HEAD_MARKER.finditer(text):
            markers += 1
            if match.group(1) != expected_head:
                violations.append(
                    f"{document.relative_to(root)}: stale Alembic head marker"
                )
        for pattern in CURRENT_HEAD_REFERENCES:
            for match in pattern.finditer(text):
                if match.group(1) != expected_head:
                    violations.append(
                        f"{document.relative_to(root)}: stale Alembic head reference"
                    )
    if markers == 0:
        violations.append("documentation has no current-alembic-head marker")
    return violations


def validate_repository_docs(root: Path = REPOSITORY_ROOT) -> list[str]:
    documents = markdown_documents(root)
    violations = broken_local_links(documents, root)
    heads = migration_heads(root / "backend" / "alembic" / "versions")
    if len(heads) != 1:
        violations.append(f"Alembic must have exactly one head; found {len(heads)}")
        return violations
    violations.extend(migration_head_reference_violations(documents, next(iter(heads)), root))
    return violations


def main() -> int:
    try:
        violations = validate_repository_docs()
    except (OSError, SyntaxError, ValueError) as exc:
        print(f"Documentation check failed: {type(exc).__name__}")
        return 1
    if violations:
        print("Documentation check failed:")
        for violation in violations:
            print(f"- {violation}")
        return 1
    head = next(iter(migration_heads()))
    print(f"Documentation check passed (Alembic head: {head}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
