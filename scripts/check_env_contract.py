"""Validate the public environment template without reading the local .env file."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from urllib.parse import urlsplit


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ENV_TEMPLATE = REPOSITORY_ROOT / ".env.example"
SETTINGS_MODULE = REPOSITORY_ROOT / "backend" / "app" / "config" / "settings.py"
COMPOSE_FILE = REPOSITORY_ROOT / "docker-compose.yml"

COMPOSE_VARIABLE = re.compile(r"\$\{([A-Z][A-Z0-9_]*)")
SENSITIVE_NAME_SUFFIXES = (
    "PASSWORD",
    "SECRET",
    "API_KEY",
    "APP_KEY",
    "CLIENT_ID",
    "SENTRY_DSN",
)
SAFE_SECRET_PLACEHOLDERS = {"", "change-me"}


def parse_env_template(path: Path) -> tuple[dict[str, str], list[str]]:
    values: dict[str, str] = {}
    violations: list[str] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            violations.append(f"line {line_number}: expected NAME=value")
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
            violations.append(f"line {line_number}: invalid variable name")
            continue
        if name in values:
            violations.append(f"{name}: duplicate template entry")
            continue
        values[name] = value.strip()
    return values, violations


def settings_variables(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Settings":
            return {
                statement.target.id.upper()
                for statement in node.body
                if isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
                and not statement.target.id.startswith("_")
            }
    raise RuntimeError("Settings class was not found")


def compose_variables(path: Path) -> set[str]:
    return set(COMPOSE_VARIABLE.findall(path.read_text(encoding="utf-8")))


def secret_placeholder_violations(values: dict[str, str]) -> list[str]:
    violations = [
        f"{name}: sensitive template values must be empty or use change-me"
        for name, value in values.items()
        if name.endswith(SENSITIVE_NAME_SUFFIXES) and value not in SAFE_SECRET_PLACEHOLDERS
    ]
    database_url = values.get("DATABASE_URL", "")
    if database_url:
        password = urlsplit(database_url).password
        if password not in SAFE_SECRET_PLACEHOLDERS:
            violations.append("DATABASE_URL: template password must use change-me")
    return violations


def validate_contract(
    template_path: Path = ENV_TEMPLATE,
    settings_path: Path = SETTINGS_MODULE,
    compose_path: Path = COMPOSE_FILE,
) -> list[str]:
    template, violations = parse_env_template(template_path)
    required = settings_variables(settings_path) | compose_variables(compose_path)
    template_names = set(template)

    violations.extend(
        f"{name}: missing from .env.example" for name in sorted(required - template_names)
    )
    violations.extend(
        f"{name}: stale .env.example entry" for name in sorted(template_names - required)
    )
    violations.extend(secret_placeholder_violations(template))
    return violations


def main() -> int:
    violations = validate_contract()
    if violations:
        print("Environment contract check failed:")
        for violation in violations:
            print(f"- {violation}")
        return 1
    print("Environment contract check passed (local .env was not read).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
