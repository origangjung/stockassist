from datetime import date

import pytest

from app.adapters.broker import BrokerAdapter
from app.config import Settings
from app.database import create_session_factory
from app.database.partitions import (
    CandlePartitionMaintenanceService,
    plan_future_partitions,
)
from app.providers.mock import MockProvider
from app.scheduler import build_scheduler


def test_future_partition_plan_crosses_year_boundary_with_exclusive_month_bounds():
    planned = plan_future_partitions(date(2026, 12, 31), 3)

    assert [item.name for item in planned] == [
        "stock_candles_2027_01",
        "stock_candles_2027_02",
        "stock_candles_2027_03",
    ]
    assert planned[0].starts_at == date(2027, 1, 1)
    assert planned[0].ends_at == date(2027, 2, 1)


def test_partition_maintenance_is_an_explicit_noop_on_sqlite(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'partitions.db'}")
    service = CandlePartitionMaintenanceService(sessions, lookahead_months=2)

    result = service.ensure_future(date(2026, 7, 16))
    status = service.status()

    assert result["status"] == "unsupported"
    assert [item["name"] for item in result["planned"]] == [
        "stock_candles_2026_08",
        "stock_candles_2026_09",
    ]
    assert status["dialect"] == "sqlite"
    assert status["items"] == []


def test_partition_scheduler_runs_immediately_then_monthly(tmp_path):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'scheduler.db'}",
        persistence_enabled=True,
        partition_maintenance_enabled=True,
        partition_lookahead_months=4,
        scheduler_enabled=False,
        realtime_enabled=False,
        stock_provider="mock",
        financial_provider="mock",
        disclosure_provider="mock",
        news_provider="mock",
        investor_flow_provider="mock",
        ai_report_provider="mock",
    )
    scheduler = build_scheduler(settings, BrokerAdapter([MockProvider()]))

    job = scheduler.get_job("stock-candle-partitions")
    assert job is not None
    assert str(job.trigger) == "cron[day='20', hour='3', minute='0']"
    assert job.next_run_time is not None


def test_partition_maintenance_requires_persistence():
    with pytest.raises(ValueError, match="PARTITION_MAINTENANCE_ENABLED"):
        Settings(
            _env_file=None,
            persistence_enabled=False,
            partition_maintenance_enabled=True,
        )
