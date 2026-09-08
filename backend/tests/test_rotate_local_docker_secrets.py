from urllib.parse import urlsplit

from scripts.operations.rotate_local_docker_secrets import rotate_env


def test_rotate_local_docker_secrets_replaces_only_weak_values(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=postgresql+psycopg://stockpilot:change-me@postgres:5432/stockpilot\n"
        "POSTGRES_PASSWORD=change-me\n"
        "ADMIN_API_KEY=\n"
        "ANALYSIS_API_KEY=already-strong-analysis-key-value-1234567890\n",
        encoding="utf-8",
    )

    rotated = rotate_env(env_file)
    values = dict(
        line.split("=", 1)
        for line in env_file.read_text(encoding="utf-8").splitlines()
    )
    database = urlsplit(values["DATABASE_URL"])

    assert "POSTGRES_PASSWORD" in rotated
    assert "ADMIN_API_KEY" in rotated
    assert "ANALYSIS_API_KEY" not in rotated
    assert len(values["POSTGRES_PASSWORD"]) >= 24
    assert database.password == values["POSTGRES_PASSWORD"]
    assert database.hostname == "postgres"
    assert values["ANALYSIS_API_KEY"] == "already-strong-analysis-key-value-1234567890"
