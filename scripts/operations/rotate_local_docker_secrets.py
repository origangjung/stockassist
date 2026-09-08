"""Generate strong local Docker secrets without printing their values."""

import argparse
from pathlib import Path
import secrets
from urllib.parse import urlsplit, urlunsplit


MAX_ENV_BYTES = 1024 * 1024
ROTATED_NAMES = (
    "POSTGRES_PASSWORD",
    "ADMIN_API_KEY",
    "ANALYSIS_API_KEY",
    "ADMIN_UI_PASSWORD",
    "GRAFANA_ADMIN_PASSWORD",
)


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description="Rotate local Docker secrets")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def _strong(value: str, minimum: int) -> bool:
    """`_strong`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return len(value) >= minimum and value.casefold() not in {
        "change-me",
        "changeme",
        "password",
    }


def _read_values(path: Path) -> tuple[list[str], dict[str, str]]:
    """`_read_values`은(는) 필요한 데이터를 조회해 반환합니다."""

    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_ENV_BYTES:
        raise ValueError("env file is missing, unsafe, or too large")
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    values: dict[str, str] = {}
    for line in lines:
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        values[name.strip()] = value
    return lines, values


def _database_url(current: str, password: str) -> str:
    """`_database_url`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    value = current or "postgresql+psycopg://stockpilot@postgres:5432/stockpilot"
    parsed = urlsplit(value)
    username = parsed.username or "stockpilot"
    host = parsed.hostname or "postgres"
    port = parsed.port or 5432
    database = parsed.path or "/stockpilot"
    return urlunsplit(
        (parsed.scheme or "postgresql+psycopg", f"{username}:{password}@{host}:{port}", database, "", "")
    )


def rotate_env(path: Path, *, force: bool = False) -> list[str]:
    """`rotate_env`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    lines, values = _read_values(path)
    generated = {
        "POSTGRES_PASSWORD": secrets.token_urlsafe(32),
        "ADMIN_API_KEY": secrets.token_hex(32),
        "ANALYSIS_API_KEY": secrets.token_hex(32),
        "ADMIN_UI_PASSWORD": secrets.token_urlsafe(32),
        "GRAFANA_ADMIN_PASSWORD": secrets.token_urlsafe(32),
    }
    minimums = {
        "POSTGRES_PASSWORD": 24,
        "ADMIN_API_KEY": 32,
        "ANALYSIS_API_KEY": 32,
        "ADMIN_UI_PASSWORD": 16,
        "GRAFANA_ADMIN_PASSWORD": 16,
    }
    updates = {
        name: value
        for name, value in generated.items()
        if force or not _strong(values.get(name, ""), minimums[name])
    }
    if "POSTGRES_PASSWORD" in updates:
        updates["DATABASE_URL"] = _database_url(
            values.get("DATABASE_URL", ""), updates["POSTGRES_PASSWORD"]
        )
    updates.setdefault("ADMIN_UI_USERNAME", values.get("ADMIN_UI_USERNAME") or "admin")

    seen: set[str] = set()
    output: list[str] = []
    for line in lines:
        name = line.split("=", 1)[0].strip() if "=" in line else ""
        if name in updates:
            output.append(f"{name}={updates[name]}")
            seen.add(name)
        else:
            output.append(line)
    for name, value in updates.items():
        if name not in seen:
            output.append(f"{name}={value}")
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text("\n".join(output) + "\n", encoding="utf-8")
    temporary.replace(path)
    return [name for name in ROTATED_NAMES if name in updates]


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    rotated = rotate_env(args.env_file.resolve(), force=args.force)
    print(f"rotated={','.join(rotated) or 'none'}")
    print("secret_values_printed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
