from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.config import get_settings


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_HEAD = "20260720_0021"


def _migration_config() -> Config:
    return Config(str(REPOSITORY_ROOT / "alembic.ini"))


def test_sqlite_migrations_round_trip_from_empty_database(tmp_path, monkeypatch):
    database_path = tmp_path / "migration-round-trip.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    overrides = {
        "APP_ENVIRONMENT": "test",
        "DATABASE_URL": database_url,
        "PERSISTENCE_ENABLED": "true",
        "STOCK_PROVIDER": "mock",
        "FINANCIAL_PROVIDER": "mock",
        "DISCLOSURE_PROVIDER": "mock",
        "NEWS_PROVIDER": "mock",
        "INVESTOR_FLOW_PROVIDER": "mock",
        "AI_REPORT_PROVIDER": "mock",
        "REALTIME_ENABLED": "false",
        "CORPORATE_ACTION_APPROVAL_ENABLED": "false",
        "MODEL_ARTIFACT_ACTIVATION_ENABLED": "false",
    }
    for name, value in overrides.items():
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()

    try:
        config = _migration_config()
        command.upgrade(config, "head")
        engine = create_engine(database_url)
        try:
            assert "stock_candles" in inspect(engine).get_table_names()
            with engine.connect() as connection:
                current = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
            assert current == EXPECTED_HEAD
        finally:
            engine.dispose()

        command.downgrade(config, "base")
        engine = create_engine(database_url)
        try:
            assert "stock_candles" not in inspect(engine).get_table_names()
        finally:
            engine.dispose()

        command.upgrade(config, "head")
        engine = create_engine(database_url)
        try:
            with engine.connect() as connection:
                current = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
            assert current == EXPECTED_HEAD
        finally:
            engine.dispose()
    finally:
        get_settings.cache_clear()
