from pathlib import Path

from scripts.check_docs import (
    broken_local_links,
    migration_head_reference_violations,
    migration_heads,
    validate_repository_docs,
)


def test_repository_documentation_links_and_head_are_current():
    assert validate_repository_docs() == []


def test_broken_link_checker_reports_missing_and_escaping_targets(tmp_path: Path):
    document = tmp_path / "README.md"
    document.write_text("[missing](missing.md)\n[escape](../outside.md)\n", encoding="utf-8")

    violations = broken_local_links([document], tmp_path)

    assert violations == [
        "README.md:1: missing local link missing.md",
        "README.md:2: link leaves repository",
    ]


def test_migration_heads_are_derived_from_revision_graph(tmp_path: Path):
    (tmp_path / "one.py").write_text(
        'revision = "one"\ndown_revision = None\n', encoding="utf-8"
    )
    (tmp_path / "two.py").write_text(
        'revision = "two"\ndown_revision = "one"\n', encoding="utf-8"
    )

    assert migration_heads(tmp_path) == {"two"}


def test_head_marker_checker_rejects_stale_marker(tmp_path: Path):
    document = tmp_path / "README.md"
    document.write_text("<!-- current-alembic-head: 20260719_0018 -->\n", encoding="utf-8")

    violations = migration_head_reference_violations([document], "20260720_0021", tmp_path)

    assert violations == ["README.md: stale Alembic head marker"]
